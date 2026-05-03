#!/usr/bin/env python3
"""
Local Resource Processor for Azure TRE (Offline Mode)

This resource processor consumes deployment messages from RabbitMQ,
executes Porter bundles to deploy/upgrade/uninstall resources,
and publishes status updates back to RabbitMQ.

Architecture:
- Listens to 'workspacequeue' for deployment requests
- Executes Porter commands (install/upgrade/uninstall)
- Publishes status updates to 'deploymentstatus' queue
- Uses Docker-in-Docker via mounted Docker socket
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4

from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractIncomingMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "tre_user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "tre_password")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

# Container Registry Configuration
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:5000")

# Queue names
RESOURCE_REQUEST_QUEUE = "workspacequeue"
DEPLOYMENT_STATUS_QUEUE = "deploymentstatus"

# Connection URL
CONNECTION_URL = (
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@"
    f"{RABBITMQ_HOST}:{RABBITMQ_PORT}{RABBITMQ_VHOST}"
)


class DockerDeploymentRunner:
    """Executes Docker Compose deployments for workspace resources."""

    @staticmethod
    async def execute_docker_action(
        action: str,
        template_path: str,
        resource_id: str,
        workspace_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a Docker Compose action (up/down).

        Args:
            action: Docker action (install, upgrade, uninstall)
            template_path: Path to docker-compose.yml
            resource_id: Resource ID
            workspace_id: Workspace ID
            parameters: Optional parameters for deployment

        Returns:
            Dict containing execution result
        """
        logger.info(f"Executing Docker {action} for resource '{resource_id}' in workspace '{workspace_id}'")

        project_name = f"{workspace_id}-{resource_id}"

        try:
            if action in ["install", "upgrade"]:
                # Docker Compose up
                cmd = [
                    "docker", "compose",
                    "-f", template_path,
                    "-p", project_name,
                    "up", "-d"
                ]

                # Set environment variables from parameters
                env = os.environ.copy()
                env["WORKSPACE_ID"] = workspace_id
                env["RESOURCE_ID"] = resource_id
                if parameters:
                    for key, value in parameters.items():
                        env[key.upper()] = str(value)

                logger.info(f"Running command: {' '.join(cmd)}")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    logger.info(f"Docker {action} succeeded for {resource_id}")
                    return {
                        "success": True,
                        "outputs": {"project_name": project_name},
                        "message": f"Successfully deployed Docker resource"
                    }
                else:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"Docker {action} failed for {resource_id}: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Failed to deploy Docker resource"
                    }

            elif action == "uninstall":
                # Docker Compose down
                cmd = [
                    "docker", "compose",
                    "-f", template_path,
                    "-p", project_name,
                    "down", "-v"  # Remove volumes
                ]

                logger.info(f"Running command: {' '.join(cmd)}")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    logger.info(f"Docker uninstall succeeded for {resource_id}")
                    return {
                        "success": True,
                        "outputs": {},
                        "message": f"Successfully removed Docker resource"
                    }
                else:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"Docker uninstall failed for {resource_id}: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Failed to remove Docker resource"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "message": f"Invalid Docker action"
                }

        except Exception as e:
            logger.error(f"Exception executing Docker {action} for {resource_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during Docker deployment"
            }


class PorterRunner:
    """Executes Porter commands for resource deployment."""

    @staticmethod
    async def execute_porter_action(
        action: str,
        bundle_name: str,
        resource_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a Porter action (install/upgrade/uninstall).

        Args:
            action: Porter action (install, upgrade, uninstall)
            bundle_name: Name of the Porter bundle
            resource_id: Resource ID for installation name
            parameters: Optional parameters for the bundle

        Returns:
            Dict containing execution result and outputs
        """
        logger.info(f"Executing Porter {action} for bundle '{bundle_name}' (resource: {resource_id})")

        # Build Porter command
        # Use local registry for bundle reference
        registry_host = REGISTRY_URL.replace("http://", "").replace("https://", "")
        bundle_reference = f"{registry_host}/{bundle_name}"

        cmd = [
            "porter", action,
            bundle_name,
            "--installation", resource_id,
            "--reference", bundle_reference,
        ]

        # Add parameters if provided
        if parameters:
            for key, value in parameters.items():
                cmd.extend(["--param", f"{key}={value}"])

        # Add common flags
        cmd.extend([
            "--allow-docker-host-access",  # Required for Docker-in-Docker
            "--debug"
        ])

        try:
            # Execute Porter command
            logger.info(f"Running command: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Porter {action} succeeded for {resource_id}")
                return {
                    "success": True,
                    "outputs": {},  # Porter outputs would be parsed here
                    "message": f"Successfully executed {action}"
                }
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Porter {action} failed for {resource_id}: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to execute {action}"
                }

        except Exception as e:
            logger.error(f"Exception executing Porter {action} for {resource_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during {action}"
            }


class ResourceProcessor:
    """Main resource processor that consumes messages and executes Porter or Docker actions."""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.porter_runner = PorterRunner()
        self.docker_runner = DockerDeploymentRunner()
        # Template path base for Docker deployments
        self.template_base = os.getenv("TEMPLATE_PATH", "/templates")

    async def connect(self):
        """Establish connection to RabbitMQ."""
        logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        self.connection = await connect_robust(CONNECTION_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        logger.info("Connected to RabbitMQ")

    async def publish_status(self, resource_id: str, status: str, message: str, outputs: Optional[Dict] = None):
        """
        Publish deployment status update to RabbitMQ.

        Args:
            resource_id: Resource ID
            status: Deployment status (deploying, deployed, failed, etc.)
            message: Status message
            outputs: Optional Porter outputs
        """
        status_message = {
            "operationId": str(uuid4()),
            "resourceId": resource_id,
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outputs": outputs or {}
        }

        # Declare status queue
        queue = await self.channel.declare_queue(DEPLOYMENT_STATUS_QUEUE, durable=True)

        # Create and publish message
        msg = Message(
            body=json.dumps(status_message).encode(),
            delivery_mode=2  # Persistent
        )

        await self.channel.default_exchange.publish(msg, routing_key=DEPLOYMENT_STATUS_QUEUE)
        logger.info(f"Published status '{status}' for resource {resource_id}")

    async def process_message(self, message: AbstractIncomingMessage):
        """
        Process a deployment request message.

        Args:
            message: Incoming RabbitMQ message
        """
        async with message.process():
            try:
                # Parse message body
                body = json.loads(message.body.decode())
                logger.info(f"Received deployment request: {body}")

                resource_id = body.get("id") or body.get("resourceId")
                action = body.get("action", "install")
                template_name = body.get("templateName", "unknown")
                template_type = body.get("templateType", "porter")  # "porter" or "docker"
                workspace_id = body.get("workspaceId", "")
                parameters = body.get("parameters", {})

                if not resource_id:
                    logger.error("Message missing required 'id' or 'resourceId' field")
                    return

                # Publish initial status
                await self.publish_status(resource_id, "deploying", f"Starting {action}")

                # Detect template type and execute appropriate action
                if template_type == "docker" or self._is_docker_template(template_name):
                    # Docker-based deployment
                    docker_compose_path = self._get_docker_template_path(template_name)

                    if not os.path.exists(docker_compose_path):
                        logger.error(f"Docker template not found: {docker_compose_path}")
                        await self.publish_status(
                            resource_id,
                            "failed",
                            f"Template not found: {template_name}"
                        )
                        return

                    result = await self.docker_runner.execute_docker_action(
                        action=action,
                        template_path=docker_compose_path,
                        resource_id=resource_id,
                        workspace_id=workspace_id,
                        parameters=parameters
                    )
                else:
                    # Porter-based deployment (existing behavior)
                    result = await self.porter_runner.execute_porter_action(
                        action=action,
                        bundle_name=template_name,
                        resource_id=resource_id,
                        parameters=parameters
                    )

                # Publish final status
                if result["success"]:
                    await self.publish_status(
                        resource_id,
                        "deployed" if action == "install" else "updated",
                        result["message"],
                        result.get("outputs")
                    )
                else:
                    await self.publish_status(
                        resource_id,
                        "failed",
                        result["message"]
                    )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message JSON: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    async def start(self):
        """Start consuming messages from RabbitMQ."""
        await self.connect()

        # Declare request queue
        queue = await self.channel.declare_queue(RESOURCE_REQUEST_QUEUE, durable=True)
        logger.info(f"Listening for messages on queue '{RESOURCE_REQUEST_QUEUE}'")

        # Start consuming
        await queue.consume(self.process_message)
        logger.info("Resource processor started successfully")

    def _is_docker_template(self, template_name: str) -> bool:
        """
        Check if template is Docker-based.

        Args:
            template_name: Template name

        Returns:
            True if Docker template exists, False otherwise
        """
        docker_path = self._get_docker_template_path(template_name)
        return os.path.exists(docker_path)

    def _get_docker_template_path(self, template_name: str) -> str:
        """
        Get path to Docker template.

        Args:
            template_name: Template name (e.g., "base-workspace", "linuxvm")

        Returns:
            Path to docker-compose.yml
        """
        # Map template names to Docker template paths
        template_map = {
            "base-workspace": f"{self.template_base}/workspaces/base/docker/docker-compose.yml",
            "linuxvm": f"{self.template_base}/workspace_services/guacamole/user_resources/guacamole-azure-linuxvm/docker/docker-compose.yml",
            "windowsvm": f"{self.template_base}/workspace_services/guacamole/user_resources/guacamole-azure-windowsvm/docker/docker-compose.yml",
        }

        return template_map.get(template_name, f"{self.template_base}/{template_name}/docker/docker-compose.yml")

    async def close(self):
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection")


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Azure TRE Local Resource Processor")
    logger.info("=" * 60)
    logger.info(f"RabbitMQ Host: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    logger.info(f"Container Registry: {REGISTRY_URL}")
    logger.info(f"Request Queue: {RESOURCE_REQUEST_QUEUE}")
    logger.info(f"Status Queue: {DEPLOYMENT_STATUS_QUEUE}")
    logger.info("=" * 60)

    processor = ResourceProcessor()

    try:
        await processor.start()
        # Keep running until interrupted
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())