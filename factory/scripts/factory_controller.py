#!/usr/bin/env python3
"""
SOFTWARE FACTORY CONTROLLER
============================
Orchestrates the assembly line for batch provisioning of LAMP stack projects.

Usage:
    python factory_controller.py batch-001.yaml
    python factory_controller.py batch-001.yaml --dry-run
    python factory_controller.py batch-001.yaml --parallel 5
"""

import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

# Optional imports - install with: pip install httpx paramiko python-dotenv
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("WARNING: httpx not installed. Run: pip install httpx")

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("WARNING: paramiko not installed. Run: pip install paramiko")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class FactoryConfig:
    """Factory configuration loaded from environment."""

    def __init__(self):
        self.digitalocean_key = os.getenv("DIGITALOCEAN_API_KEY", "")
        self.vultr_key = os.getenv("VULTR_API_KEY", "")
        self.cloudflare_key = os.getenv("CLOUDFLARE_API_KEY", "")
        self.cloudflare_zone = os.getenv("CLOUDFLARE_ZONE_ID", "")
        self.skyvern_url = os.getenv("SKYVERN_API_URL", "http://localhost:8000")
        self.skyvern_key = os.getenv("SKYVERN_API_KEY", "")
        self.ssh_key_path = os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa")
        self.template_repo = os.getenv(
            "TEMPLATE_REPO",
            "https://github.com/yourusername/lamp-saas-template.git"
        )

    def validate(self) -> List[str]:
        """Validate required configuration. Returns list of missing items."""
        missing = []
        if not self.digitalocean_key and not self.vultr_key:
            missing.append("DIGITALOCEAN_API_KEY or VULTR_API_KEY")
        if not self.cloudflare_key:
            missing.append("CLOUDFLARE_API_KEY")
        if not self.cloudflare_zone:
            missing.append("CLOUDFLARE_ZONE_ID")
        return missing


class SkyvernClient:
    """Client for Skyvern browser automation API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def health_check(self) -> bool:
        """Check if Skyvern is running."""
        if not HTTPX_AVAILABLE:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/health", timeout=5)
                return resp.status_code == 200
        except Exception:
            return False

    async def run_workflow(self, workflow_name: str, params: Dict) -> Dict:
        """Execute a Skyvern workflow."""
        if not HTTPX_AVAILABLE:
            return {"error": "httpx not installed"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/workflows/{workflow_name}/run",
                headers=self.headers,
                json=params,
                timeout=300  # 5 min timeout for browser tasks
            )
            return resp.json()

    async def navigate_and_click(
        self,
        url: str,
        instructions: str
    ) -> Dict:
        """Send a simple navigation task to Skyvern."""
        if not HTTPX_AVAILABLE:
            return {"error": "httpx not installed"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/tasks",
                headers=self.headers,
                json={
                    "url": url,
                    "instructions": instructions,
                    "max_steps": 20,
                    "timeout": 120
                },
                timeout=300
            )
            return resp.json()


class DigitalOceanClient:
    """Client for DigitalOcean API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.digitalocean.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def create_droplet(
        self,
        name: str,
        region: str = "nyc3",
        size: str = "s-1vcpu-1gb",
        image: str = "ubuntu-22-04-x64",
        ssh_keys: List[str] = None
    ) -> Dict:
        """Create a new droplet."""
        if not HTTPX_AVAILABLE:
            return {"error": "httpx not installed"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/droplets",
                headers=self.headers,
                json={
                    "name": name,
                    "region": region,
                    "size": size,
                    "image": image,
                    "ssh_keys": ssh_keys or [],
                    "tags": ["factory", "lamp"]
                },
                timeout=60
            )
            return resp.json()

    async def get_droplet(self, droplet_id: int) -> Dict:
        """Get droplet details."""
        if not HTTPX_AVAILABLE:
            return {"error": "httpx not installed"}

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/droplets/{droplet_id}",
                headers=self.headers,
                timeout=30
            )
            return resp.json()

    async def wait_for_ip(self, droplet_id: int, timeout: int = 120) -> str:
        """Wait for droplet to get an IP address."""
        start = time.time()
        while time.time() - start < timeout:
            data = await self.get_droplet(droplet_id)
            if "droplet" in data:
                networks = data["droplet"].get("networks", {})
                v4 = networks.get("v4", [])
                for net in v4:
                    if net.get("type") == "public":
                        return net.get("ip_address")
            await asyncio.sleep(5)
        raise TimeoutError(f"Droplet {droplet_id} did not get IP in {timeout}s")

    async def list_ssh_keys(self) -> List[Dict]:
        """List SSH keys on account."""
        if not HTTPX_AVAILABLE:
            return []

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/account/keys",
                headers=self.headers,
                timeout=30
            )
            data = resp.json()
            return data.get("ssh_keys", [])


class CloudflareClient:
    """Client for Cloudflare API."""

    def __init__(self, api_key: str, zone_id: str):
        self.api_key = api_key
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def create_a_record(
        self,
        name: str,
        content: str,
        proxied: bool = True
    ) -> Dict:
        """Create an A record."""
        if not HTTPX_AVAILABLE:
            return {"error": "httpx not installed"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/zones/{self.zone_id}/dns_records",
                headers=self.headers,
                json={
                    "type": "A",
                    "name": name,
                    "content": content,
                    "ttl": 1,  # Auto
                    "proxied": proxied
                },
                timeout=30
            )
            return resp.json()


class SSHConnection:
    """SSH connection manager for server setup."""

    def __init__(self, host: str, username: str = "root", key_path: str = None):
        self.host = host
        self.username = username
        self.key_path = os.path.expanduser(key_path or "~/.ssh/id_rsa")
        self.client = None

    async def connect(self):
        """Establish SSH connection."""
        if not PARAMIKO_AVAILABLE:
            raise RuntimeError("paramiko not installed")

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Run in thread pool to not block
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.connect(
                self.host,
                username=self.username,
                key_filename=self.key_path,
                timeout=30
            )
        )

    async def run_command(self, command: str) -> tuple:
        """Run a command and return (stdout, stderr, exit_code)."""
        if not self.client:
            await self.connect()

        loop = asyncio.get_event_loop()

        def execute():
            stdin, stdout, stderr = self.client.exec_command(command, timeout=300)
            exit_code = stdout.channel.recv_exit_status()
            return stdout.read().decode(), stderr.read().decode(), exit_code

        return await loop.run_in_executor(None, execute)

    async def run_script(self, script_content: str) -> tuple:
        """Upload and run a script."""
        # Upload script
        sftp = self.client.open_sftp()
        script_path = "/tmp/factory_script.sh"

        with sftp.file(script_path, "w") as f:
            f.write(script_content)

        sftp.chmod(script_path, 0o755)
        sftp.close()

        # Run script
        return await self.run_command(f"bash {script_path}")

    def close(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()


class Project:
    """Represents a project being built."""

    def __init__(self, data: Dict):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.domain = data.get("domain", "")
        self.client_name = data.get("client", "")
        self.template = data.get("type", "saas-template-base")
        self.server_size = data.get("server_size", "s-1vcpu-1gb")
        self.region = data.get("region", "nyc3")

        # Populated during processing
        self.server_id = None
        self.server_ip = None
        self.db_name = None
        self.db_user = None
        self.db_pass = None
        self.status = "pending"
        self.errors = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "client": self.client_name,
            "server_ip": self.server_ip,
            "status": self.status,
            "errors": self.errors
        }


class SoftwareFactory:
    """Main factory controller."""

    def __init__(self, config: FactoryConfig):
        self.config = config
        self.do_client = DigitalOceanClient(config.digitalocean_key)
        self.cf_client = CloudflareClient(
            config.cloudflare_key,
            config.cloudflare_zone
        )
        self.skyvern = SkyvernClient(config.skyvern_url, config.skyvern_key)

    async def process_batch(
        self,
        batch_file: str,
        dry_run: bool = False,
        parallel: int = 10
    ) -> Dict:
        """Process a batch of projects."""

        print("\n" + "=" * 60)
        print("  SOFTWARE FACTORY - BATCH PROCESSING")
        print("=" * 60)

        # Load batch file
        with open(batch_file) as f:
            batch_data = yaml.safe_load(f)

        batch_id = batch_data.get("batch_id", "unknown")
        projects = [Project(p) for p in batch_data.get("projects", [])]

        print(f"\nBatch ID: {batch_id}")
        print(f"Projects: {len(projects)}")
        print(f"Parallel: {parallel}")
        print(f"Dry Run: {dry_run}")

        if dry_run:
            print("\n[DRY RUN] Would process these projects:")
            for p in projects:
                print(f"  - {p.id}: {p.name} ({p.domain})")
            return {"status": "dry_run", "projects": len(projects)}

        start_time = time.time()
        results = []

        # Process in batches
        for i in range(0, len(projects), parallel):
            batch_projects = projects[i:i + parallel]
            print(f"\n--- Processing batch {i // parallel + 1} ---")

            # Station 1: Provision servers
            print("\n[STATION 1] Provisioning servers...")
            provision_tasks = [
                self.provision_server(p) for p in batch_projects
            ]
            await asyncio.gather(*provision_tasks, return_exceptions=True)

            # Wait for IPs
            print("\n[STATION 1b] Waiting for server IPs...")
            ip_tasks = [self.wait_for_server_ip(p) for p in batch_projects]
            await asyncio.gather(*ip_tasks, return_exceptions=True)

            # Station 2: Configure DNS
            print("\n[STATION 2] Configuring DNS...")
            dns_tasks = [self.configure_dns(p) for p in batch_projects]
            await asyncio.gather(*dns_tasks, return_exceptions=True)

            # Station 3: Setup LAMP
            print("\n[STATION 3] Installing LAMP stack...")
            lamp_tasks = [self.setup_lamp(p) for p in batch_projects]
            await asyncio.gather(*lamp_tasks, return_exceptions=True)

            # Station 4: Create databases
            print("\n[STATION 4] Creating databases...")
            db_tasks = [self.setup_database(p) for p in batch_projects]
            await asyncio.gather(*db_tasks, return_exceptions=True)

            # Station 5: Deploy application
            print("\n[STATION 5] Deploying applications...")
            deploy_tasks = [self.deploy_application(p) for p in batch_projects]
            await asyncio.gather(*deploy_tasks, return_exceptions=True)

            # Station 6: SSL certificates
            print("\n[STATION 6] Setting up SSL...")
            ssl_tasks = [self.setup_ssl(p) for p in batch_projects]
            await asyncio.gather(*ssl_tasks, return_exceptions=True)

            # Station 7: Health checks
            print("\n[STATION 7] Running health checks...")
            health_tasks = [self.health_check(p) for p in batch_projects]
            await asyncio.gather(*health_tasks, return_exceptions=True)

            results.extend(batch_projects)

        elapsed = time.time() - start_time

        # Generate report
        report = self.generate_report(batch_id, results, elapsed)
        return report

    async def provision_server(self, project: Project):
        """Provision a server for the project."""
        try:
            print(f"  Provisioning {project.id}...")

            # Get SSH keys
            ssh_keys = await self.do_client.list_ssh_keys()
            key_ids = [str(k["id"]) for k in ssh_keys]

            # Create droplet
            result = await self.do_client.create_droplet(
                name=f"{project.id}-{project.name}",
                region=project.region,
                size=project.server_size,
                ssh_keys=key_ids
            )

            if "droplet" in result:
                project.server_id = result["droplet"]["id"]
                print(f"  ✓ {project.id} - Droplet ID: {project.server_id}")
            else:
                project.errors.append(f"Provision failed: {result}")
                project.status = "error"

        except Exception as e:
            project.errors.append(f"Provision error: {str(e)}")
            project.status = "error"

    async def wait_for_server_ip(self, project: Project):
        """Wait for server to get IP address."""
        if not project.server_id or project.status == "error":
            return

        try:
            project.server_ip = await self.do_client.wait_for_ip(
                project.server_id,
                timeout=120
            )
            print(f"  ✓ {project.id} - IP: {project.server_ip}")
        except Exception as e:
            project.errors.append(f"IP timeout: {str(e)}")
            project.status = "error"

    async def configure_dns(self, project: Project):
        """Configure DNS for the project."""
        if not project.server_ip or project.status == "error":
            return

        try:
            # Extract subdomain from domain
            subdomain = project.domain.split(".")[0]

            result = await self.cf_client.create_a_record(
                name=subdomain,
                content=project.server_ip,
                proxied=True
            )

            if result.get("success"):
                print(f"  ✓ {project.id} - DNS configured")
            else:
                project.errors.append(f"DNS failed: {result}")

        except Exception as e:
            project.errors.append(f"DNS error: {str(e)}")

    async def setup_lamp(self, project: Project):
        """Install LAMP stack on server."""
        if not project.server_ip or project.status == "error":
            return

        try:
            # Wait for server to be ready for SSH
            await asyncio.sleep(30)

            ssh = SSHConnection(
                project.server_ip,
                key_path=self.config.ssh_key_path
            )

            await ssh.connect()

            # Run LAMP setup script
            lamp_script = self.get_lamp_script()
            stdout, stderr, exit_code = await ssh.run_script(lamp_script)

            ssh.close()

            if exit_code == 0:
                print(f"  ✓ {project.id} - LAMP installed")
            else:
                project.errors.append(f"LAMP install failed: {stderr}")

        except Exception as e:
            project.errors.append(f"LAMP error: {str(e)}")

    async def setup_database(self, project: Project):
        """Create database and user."""
        if not project.server_ip or project.status == "error":
            return

        try:
            ssh = SSHConnection(
                project.server_ip,
                key_path=self.config.ssh_key_path
            )
            await ssh.connect()

            db_script = self.get_database_script(project.name)
            stdout, stderr, exit_code = await ssh.run_script(db_script)

            ssh.close()

            if exit_code == 0:
                # Parse credentials from output
                for line in stdout.split("\n"):
                    if line.startswith("DB_NAME="):
                        project.db_name = line.split("=")[1]
                    elif line.startswith("DB_USER="):
                        project.db_user = line.split("=")[1]
                    elif line.startswith("DB_PASS="):
                        project.db_pass = line.split("=")[1]

                print(f"  ✓ {project.id} - Database created")
            else:
                project.errors.append(f"DB setup failed: {stderr}")

        except Exception as e:
            project.errors.append(f"DB error: {str(e)}")

    async def deploy_application(self, project: Project):
        """Deploy application files."""
        if not project.server_ip or project.status == "error":
            return

        try:
            ssh = SSHConnection(
                project.server_ip,
                key_path=self.config.ssh_key_path
            )
            await ssh.connect()

            deploy_script = self.get_deploy_script(project)
            stdout, stderr, exit_code = await ssh.run_script(deploy_script)

            ssh.close()

            if exit_code == 0:
                print(f"  ✓ {project.id} - Application deployed")
            else:
                project.errors.append(f"Deploy failed: {stderr}")

        except Exception as e:
            project.errors.append(f"Deploy error: {str(e)}")

    async def setup_ssl(self, project: Project):
        """Setup SSL certificate."""
        if not project.server_ip or project.status == "error":
            return

        try:
            ssh = SSHConnection(
                project.server_ip,
                key_path=self.config.ssh_key_path
            )
            await ssh.connect()

            ssl_script = self.get_ssl_script(project.domain)
            stdout, stderr, exit_code = await ssh.run_script(ssl_script)

            ssh.close()

            if exit_code == 0:
                print(f"  ✓ {project.id} - SSL configured")
            else:
                # SSL might fail if DNS hasn't propagated yet
                project.errors.append(f"SSL warning: {stderr}")

        except Exception as e:
            project.errors.append(f"SSL error: {str(e)}")

    async def health_check(self, project: Project):
        """Verify project is working."""
        if project.status == "error":
            return

        try:
            if not HTTPX_AVAILABLE:
                project.status = "ready"
                return

            async with httpx.AsyncClient(verify=False) as client:
                url = f"https://{project.domain}"
                resp = await client.get(url, timeout=30, follow_redirects=True)

                if resp.status_code == 200:
                    project.status = "ready"
                    print(f"  ✓ {project.id} - HEALTHY")
                else:
                    project.status = "warning"
                    project.errors.append(f"HTTP {resp.status_code}")

        except Exception as e:
            project.status = "warning"
            project.errors.append(f"Health check: {str(e)}")

    def get_lamp_script(self) -> str:
        """Return LAMP installation script."""
        return """#!/bin/bash
set -e

apt update && apt upgrade -y

# Apache
apt install -y apache2
systemctl enable apache2
a2enmod rewrite ssl headers deflate expires

# MariaDB
apt install -y mariadb-server mariadb-client
TEMP_ROOT_PASS=$(openssl rand -base64 24)
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${TEMP_ROOT_PASS}';"
mysql -e "DELETE FROM mysql.user WHERE User='';"
mysql -e "FLUSH PRIVILEGES;"
echo "${TEMP_ROOT_PASS}" > /root/.mariadb_temp_pass
chmod 600 /root/.mariadb_temp_pass

# PHP
apt install -y software-properties-common
add-apt-repository -y ppa:ondrej/php
apt update
apt install -y php8.2 php8.2-{cli,fpm,mysql,mbstring,xml,curl,gd,zip,intl,bcmath}
a2enmod php8.2
systemctl restart apache2

# Composer
curl -sS https://getcomposer.org/installer | php
mv composer.phar /usr/local/bin/composer

# Certbot
apt install -y certbot python3-certbot-apache

# Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Web directory
mkdir -p /var/www/app
chown -R www-data:www-data /var/www/app

echo "LAMP_SETUP_COMPLETE"
"""

    def get_database_script(self, project_name: str) -> str:
        """Return database setup script."""
        return f"""#!/bin/bash
set -e

PROJECT_NAME="{project_name.replace('-', '_')}"
DB_NAME="${{PROJECT_NAME}}_prod"
DB_USER="${{PROJECT_NAME}}_user"
DB_PASS=$(openssl rand -base64 24)

ROOT_PASS=$(cat /root/.mariadb_temp_pass)

mysql -u root -p"${{ROOT_PASS}}" << EOF
CREATE DATABASE IF NOT EXISTS ${{DB_NAME}}
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${{DB_USER}}'@'localhost'
  IDENTIFIED BY '${{DB_PASS}}';

GRANT ALL PRIVILEGES ON ${{DB_NAME}}.* TO '${{DB_USER}}'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "DB_NAME=${{DB_NAME}}"
echo "DB_USER=${{DB_USER}}"
echo "DB_PASS=${{DB_PASS}}"
"""

    def get_deploy_script(self, project: Project) -> str:
        """Return application deployment script."""
        return f"""#!/bin/bash
set -e

APP_DIR="/var/www/app"
TEMPLATE_REPO="{self.config.template_repo}"

# Clone template
git clone ${{TEMPLATE_REPO}} ${{APP_DIR}} || true

cd ${{APP_DIR}}

# Install dependencies
if [ -f composer.json ]; then
    composer install --no-dev --optimize-autoloader
fi

# Set permissions
chown -R www-data:www-data ${{APP_DIR}}
chmod -R 755 ${{APP_DIR}}
mkdir -p ${{APP_DIR}}/uploads ${{APP_DIR}}/logs
chmod -R 775 ${{APP_DIR}}/uploads ${{APP_DIR}}/logs

# Configure Apache vhost
cat > /etc/apache2/sites-available/{project.domain}.conf << 'VHOST'
<VirtualHost *:80>
    ServerName {project.domain}
    DocumentRoot /var/www/app

    <Directory /var/www/app>
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${{APACHE_LOG_DIR}}/{project.domain}_error.log
    CustomLog ${{APACHE_LOG_DIR}}/{project.domain}_access.log combined
</VirtualHost>
VHOST

a2ensite {project.domain}.conf
a2dissite 000-default.conf || true
systemctl reload apache2

echo "DEPLOY_COMPLETE"
"""

    def get_ssl_script(self, domain: str) -> str:
        """Return SSL setup script."""
        return f"""#!/bin/bash
set -e

certbot --apache \
    --non-interactive \
    --agree-tos \
    --email ssl@{domain.split('.', 1)[1] if '.' in domain else domain} \
    --domains {domain} \
    --redirect || echo "SSL_PENDING"
"""

    def generate_report(
        self,
        batch_id: str,
        projects: List[Project],
        elapsed: float
    ) -> Dict:
        """Generate batch completion report."""

        ready = sum(1 for p in projects if p.status == "ready")
        warnings = sum(1 for p in projects if p.status == "warning")
        errors = sum(1 for p in projects if p.status == "error")

        report = {
            "batch_id": batch_id,
            "completed_at": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "elapsed_minutes": round(elapsed / 60, 2),
            "summary": {
                "total": len(projects),
                "ready": ready,
                "warnings": warnings,
                "errors": errors
            },
            "projects": [p.to_dict() for p in projects]
        }

        # Print report
        print("\n" + "=" * 60)
        print("  BATCH COMPLETE")
        print("=" * 60)
        print(f"\nBatch ID: {batch_id}")
        print(f"Duration: {report['elapsed_minutes']} minutes")
        print(f"\nResults:")
        print(f"  ✓ Ready:    {ready}")
        print(f"  ⚠ Warnings: {warnings}")
        print(f"  ✗ Errors:   {errors}")
        print("\nProjects:")
        for p in projects:
            icon = "✓" if p.status == "ready" else "⚠" if p.status == "warning" else "✗"
            print(f"  {icon} {p.id}: {p.domain} ({p.status})")
            if p.errors:
                for err in p.errors:
                    print(f"      - {err}")

        print("\n" + "=" * 60)

        # Save report
        report_path = f"reports/batch-{batch_id}-{int(time.time())}.json"
        os.makedirs("reports", exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved: {report_path}")

        return report


def main():
    parser = argparse.ArgumentParser(description="Software Factory Controller")
    parser.add_argument("batch_file", help="Path to batch YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--parallel", type=int, default=10, help="Max parallel projects")

    args = parser.parse_args()

    # Load and validate config
    config = FactoryConfig()
    missing = config.validate()
    if missing and not args.dry_run:
        print("ERROR: Missing required configuration:")
        for item in missing:
            print(f"  - {item}")
        print("\nSet these in .env file or environment variables.")
        sys.exit(1)

    # Run factory
    factory = SoftwareFactory(config)

    try:
        result = asyncio.run(factory.process_batch(
            args.batch_file,
            dry_run=args.dry_run,
            parallel=args.parallel
        ))
        sys.exit(0 if result.get("summary", {}).get("errors", 0) == 0 else 1)
    except KeyboardInterrupt:
        print("\nAborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
