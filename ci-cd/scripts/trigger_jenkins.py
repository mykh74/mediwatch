#!/usr/bin/env python3
"""
Jenkins Build Trigger Script

This script triggers Jenkins builds remotely and can be used from:
- Airflow DAGs
- Command line
- Other automation scripts
- Monitoring systems

Usage:
    python trigger_jenkins.py --job mediwatch-ci-cd --token TOKEN
    python trigger_jenkins.py --job mediwatch-ci-cd --token TOKEN --deploy-mode kubernetes
    
    # From Python code:
    from trigger_jenkins import trigger_jenkins_build
    build_number = trigger_jenkins_build(
        job_name="mediwatch-ci-cd",
        token="mediwatch-build-token",
        parameters={"DEPLOY_MODE": "docker"}
    )
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Optional
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JenkinsTrigger:
    """Jenkins remote trigger client."""
    
    def __init__(
        self,
        jenkins_url: str = "http://localhost:8080",
        username: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        """
        Initialize Jenkins trigger client.
        
        Args:
            jenkins_url: Base URL of Jenkins server
            username: Jenkins username (optional, for auth)
            api_token: Jenkins API token (optional, for auth)
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        
        if username and api_token:
            self.session.auth = (username, api_token)
            logger.info(f"Using authentication for user: {username}")
    
    def trigger_build(
        self,
        job_name: str,
        token: Optional[str] = None,
        parameters: Optional[Dict[str, any]] = None,
        wait: bool = False,
        timeout: int = 300
    ) -> Optional[int]:
        """
        Trigger a Jenkins build.
        
        Args:
            job_name: Name of the Jenkins job
            token: Build trigger token (alternative to user auth)
            parameters: Build parameters as dictionary
            wait: Whether to wait for build to complete
            timeout: Max seconds to wait for build completion
            
        Returns:
            Build number if successful, None otherwise
        """
        # Construct trigger URL
        if parameters:
            endpoint = f"{self.jenkins_url}/job/{job_name}/buildWithParameters"
        else:
            endpoint = f"{self.jenkins_url}/job/{job_name}/build"
        
        # Prepare parameters
        params = parameters.copy() if parameters else {}
        if token:
            params['token'] = token
        
        # Make request
        try:
            logger.info(f"Triggering Jenkins job: {job_name}")
            if params:
                logger.info(f"Parameters: {json.dumps(params, indent=2)}")
            
            response = self.session.post(
                endpoint,
                params=params,
                timeout=30
            )
            
            if response.status_code == 201:
                logger.info("✓ Build triggered successfully!")
                
                # Get build number from queue
                queue_url = response.headers.get('Location')
                if queue_url and wait:
                    build_number = self._wait_for_build(queue_url, timeout)
                    return build_number
                
                return self._get_next_build_number(job_name)
                
            elif response.status_code == 401:
                logger.error("✗ Authentication failed. Check credentials or token.")
                return None
                
            elif response.status_code == 404:
                logger.error(f"✗ Job not found: {job_name}")
                return None
                
            else:
                logger.error(f"✗ Failed to trigger build. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Cannot connect to Jenkins at {self.jenkins_url}")
            logger.error("  Make sure Jenkins is running and accessible.")
            return None
            
        except requests.exceptions.Timeout:
            logger.error("✗ Request timed out")
            return None
            
        except Exception as e:
            logger.error(f"✗ Error triggering build: {e}")
            return None
    
    def _get_next_build_number(self, job_name: str) -> Optional[int]:
        """Get the next build number for a job."""
        try:
            url = f"{self.jenkins_url}/job/{job_name}/api/json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                next_build = data.get('nextBuildNumber')
                logger.info(f"Build number: #{next_build}")
                return next_build
            
        except Exception as e:
            logger.warning(f"Could not get build number: {e}")
        
        return None
    
    def _wait_for_build(self, queue_url: str, timeout: int) -> Optional[int]:
        """Wait for queued build to start and return build number."""
        logger.info("Waiting for build to start...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Get queue item info
                response = self.session.get(f"{queue_url}api/json", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if build has started
                    if 'executable' in data:
                        build_number = data['executable']['number']
                        build_url = data['executable']['url']
                        logger.info(f"✓ Build started: #{build_number}")
                        logger.info(f"  URL: {build_url}")
                        return build_number
                    
                    # Still in queue
                    why = data.get('why', 'Waiting in queue')
                    logger.info(f"  Status: {why}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"Error checking build status: {e}")
                time.sleep(2)
        
        logger.warning("Build did not start within timeout period")
        return None
    
    def get_build_status(self, job_name: str, build_number: int) -> Optional[Dict]:
        """
        Get status of a specific build.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            
        Returns:
            Build information dictionary
        """
        try:
            url = f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'number': data.get('number'),
                    'result': data.get('result'),
                    'building': data.get('building'),
                    'duration': data.get('duration'),
                    'url': data.get('url')
                }
            
        except Exception as e:
            logger.error(f"Error getting build status: {e}")
        
        return None
    
    def wait_for_completion(
        self,
        job_name: str,
        build_number: int,
        timeout: int = 600,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for a build to complete.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number to monitor
            timeout: Maximum seconds to wait
            poll_interval: Seconds between status checks
            
        Returns:
            True if build succeeded, False otherwise
        """
        logger.info(f"Monitoring build #{build_number}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_build_status(job_name, build_number)
            
            if not status:
                logger.error("Could not get build status")
                return False
            
            if not status['building']:
                result = status['result']
                duration = status['duration'] / 1000  # Convert to seconds
                
                if result == 'SUCCESS':
                    logger.info(f"✓ Build completed successfully in {duration:.1f}s")
                    return True
                else:
                    logger.error(f"✗ Build failed with result: {result}")
                    logger.error(f"  Check logs: {status['url']}console")
                    return False
            
            # Still building
            logger.info(f"  Building... ({int(time.time() - start_time)}s)")
            time.sleep(poll_interval)
        
        logger.warning("Build did not complete within timeout")
        return False


def trigger_jenkins_build(
    jenkins_url: str = "http://localhost:8080",
    job_name: str = "mediwatch-ci-cd",
    token: Optional[str] = None,
    username: Optional[str] = None,
    api_token: Optional[str] = None,
    parameters: Optional[Dict] = None,
    wait: bool = False,
    timeout: int = 300
) -> Optional[int]:
    """
    Convenience function to trigger a Jenkins build.
    
    Args:
        jenkins_url: Jenkins server URL
        job_name: Job name to trigger
        token: Build trigger token
        username: Jenkins username (alternative auth)
        api_token: Jenkins API token (alternative auth)
        parameters: Build parameters
        wait: Wait for build to start
        timeout: Timeout for waiting
    
    Returns:
        Build number if successful
    
    Example:
        >>> build_number = trigger_jenkins_build(
        ...     job_name="mediwatch-ci-cd",
        ...     token="mediwatch-build-token",
        ...     parameters={"DEPLOY_MODE": "docker", "RUN_TESTS": True}
        ... )
    """
    client = JenkinsTrigger(jenkins_url, username, api_token)
    return client.trigger_build(job_name, token, parameters, wait, timeout)


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Trigger Jenkins builds remotely",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using build token
  %(prog)s --job mediwatch-ci-cd --token mediwatch-build-token
  
  # With parameters
  %(prog)s --job mediwatch-ci-cd --token TOKEN --deploy-mode docker --run-tests
  
  # Using user authentication
  %(prog)s --job mediwatch-ci-cd --username admin --api-token YOUR_TOKEN
  
  # Wait for build to complete
  %(prog)s --job mediwatch-ci-cd --token TOKEN --wait --monitor
        """
    )
    
    # Connection settings
    parser.add_argument(
        '--jenkins-url',
        default='http://localhost:8080',
        help='Jenkins server URL (default: http://localhost:8080)'
    )
    parser.add_argument(
        '--job',
        required=True,
        help='Jenkins job name'
    )
    
    # Authentication
    auth_group = parser.add_argument_group('authentication')
    auth_group.add_argument(
        '--token',
        help='Build trigger token (from job configuration)'
    )
    auth_group.add_argument(
        '--username',
        help='Jenkins username (for API authentication)'
    )
    auth_group.add_argument(
        '--api-token',
        help='Jenkins API token (for API authentication)'
    )
    
    # Build parameters
    params_group = parser.add_argument_group('build parameters')
    params_group.add_argument(
        '--deploy-mode',
        choices=['docker', 'kubernetes'],
        help='Deployment mode'
    )
    params_group.add_argument(
        '--run-tests',
        action='store_true',
        help='Run tests before deployment'
    )
    params_group.add_argument(
        '--no-tests',
        action='store_true',
        help='Skip tests'
    )
    params_group.add_argument(
        '--force-rebuild',
        action='store_true',
        help='Force rebuild even if image exists'
    )
    params_group.add_argument(
        '--custom-tag',
        help='Custom Docker image tag'
    )
    
    # Monitoring
    monitor_group = parser.add_argument_group('monitoring')
    monitor_group.add_argument(
        '--wait',
        action='store_true',
        help='Wait for build to start'
    )
    monitor_group.add_argument(
        '--monitor',
        action='store_true',
        help='Monitor build until completion'
    )
    monitor_group.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Timeout in seconds (default: 600)'
    )
    
    args = parser.parse_args()
    
    # Build parameters
    parameters = {}
    if args.deploy_mode:
        parameters['DEPLOY_MODE'] = args.deploy_mode
    if args.run_tests:
        parameters['RUN_TESTS'] = 'true'
    if args.no_tests:
        parameters['RUN_TESTS'] = 'false'
    if args.force_rebuild:
        parameters['FORCE_REBUILD'] = 'true'
    if args.custom_tag:
        parameters['CUSTOM_TAG'] = args.custom_tag
    
    # Create client and trigger build
    client = JenkinsTrigger(
        jenkins_url=args.jenkins_url,
        username=args.username,
        api_token=args.api_token
    )
    
    build_number = client.trigger_build(
        job_name=args.job,
        token=args.token,
        parameters=parameters if parameters else None,
        wait=args.wait or args.monitor,
        timeout=args.timeout
    )
    
    if not build_number:
        sys.exit(1)
    
    # Monitor build if requested
    if args.monitor:
        success = client.wait_for_completion(
            job_name=args.job,
            build_number=build_number,
            timeout=args.timeout
        )
        sys.exit(0 if success else 1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
