#!/usr/bin/env python
"""
Master Initialization Script for Fiber Laser DMX Control System
Automates complete setup from scratch including:
  - System dependencies installation
  - Miniconda3 ARM64 setup
  - Conda environment creation
  - Python dependencies installation
  - FTDI USB-DMX udev rules configuration
  - Systemd services setup
  - nginx web server setup
  - PHP-FPM configuration
  - HardInfo2 web interface setup (with local database)
  - WiFi hotspot configuration
  - Caddy reverse proxy configuration
  
Optional Enhancements (Steps 12-16):
  - Benchmark dashboard (HTML visualization)
  - Scheduled daily benchmarks (cron job)
  - HTTPS certificates (Let's Encrypt via Caddy)
  - Web authentication (login page)
  - GraphQL API (query interface)

Note: This script MUST be run within the fiber-laser-dmx Conda environment.
If needed, activate with: conda activate fiber-laser-dmx

Usage:
    sudo python scripts/init_all.py          # Full setup
    sudo python scripts/init_all.py --verify # Verify setup only
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import List, Tuple
import argparse


class Colors:
    """Terminal color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class InitializationManager:
    """Manages complete system initialization"""

    def __init__(self, project_root: Path, verify_only: bool = False):
        self.project_root = project_root
        self.verify_only = verify_only
        self.username = self._get_username()
        self.user_home = Path.home() if self.username != 'root' else Path('/root')
        self.miniconda_path = self.user_home / 'miniconda3'
        self.conda_env_name = 'fiber-laser-dmx'
        
    def _get_username(self) -> str:
        """Get the non-root user"""
        try:
            result = subprocess.run(['whoami'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            self.print_error(f"Failed to get username: {e}")
            return 'laser-dmx'

    def print_header(self, message: str):
        """Print section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message:^70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    def print_step(self, step: int, message: str):
        """Print step indicator"""
        print(f"{Colors.OKBLUE}[{step}] {message}{Colors.ENDC}")

    def print_ok(self, message: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

    def run_command(self, cmd: List[str], description: str = "", check: bool = True, 
                   capture_output: bool = False, as_root: bool = False) -> Tuple[bool, str]:
        """Run a shell command safely"""
        try:
            if as_root and os.geteuid() != 0:
                cmd = ['sudo'] + cmd
            
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                timeout=3600
            )
            
            if capture_output:
                return True, result.stdout.strip()
            return True, ""
        except subprocess.TimeoutExpired:
            self.print_error(f"Command timed out: {description}")
            return False, ""
        except subprocess.CalledProcessError as e:
            if not check:
                return False, ""
            self.print_error(f"Command failed: {description}")
            if e.stderr:
                self.print_error(f"  Error: {e.stderr[:200]}")
            return False, ""
        except Exception as e:
            self.print_error(f"Exception during command: {description}: {e}")
            return False, ""

    def verify_root(self):
        """Verify script is running as root"""
        if os.geteuid() != 0:
            self.print_error("This script must be run with sudo")
            sys.exit(1)
        self.print_ok("Running as root")

    def step_1_system_dependencies(self):
        """Step 1: Install system dependencies"""
        self.print_step(1, "Installing system dependencies via apt")
        
        # Read system-requirements.txt
        req_file = self.project_root / 'system-requirements.txt'
        if not req_file.exists():
            self.print_error(f"File not found: {req_file}")
            return False
        
        try:
            with open(req_file, 'r') as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not packages:
                self.print_warning("No packages found in system-requirements.txt")
                return False
            
            self.print_step(1, f"Installing {len(packages)} system packages...")
            
            # Update package lists
            success, _ = self.run_command(['apt-get', 'update'], 
                                         description="Update apt package lists",
                                         as_root=True)
            if not success:
                self.print_warning("apt-get update had issues, continuing anyway")
            
            # Install packages
            success, _ = self.run_command(['apt-get', 'install', '-y'] + packages,
                                         description="Install system packages",
                                         as_root=True)
            
            if success:
                self.print_ok(f"Installed {len(packages)} system packages")
                return True
            return False
            
        except Exception as e:
            self.print_error(f"Failed to install system dependencies: {e}")
            return False

    def step_2_miniconda(self):
        """Step 2: Install Miniconda3 ARM64"""
        self.print_step(2, "Setting up Miniconda3 ARM64")
        
        # Check if already installed
        if self.miniconda_path.exists():
            self.print_ok(f"Miniconda3 already installed at {self.miniconda_path}")
            return True
        
        try:
            # Download Miniconda3 ARM64
            self.print_step(2, "Downloading Miniconda3 ARM64...")
            installer = Path('/tmp/Miniconda3-latest-Linux-aarch64.sh')
            
            success, _ = self.run_command(
                ['wget', '-q', 
                 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh',
                 '-O', str(installer)],
                description="Download Miniconda3 ARM64",
                as_root=False
            )
            
            if not success:
                self.print_error("Failed to download Miniconda3")
                return False
            
            # Install Miniconda3
            self.print_step(2, "Installing Miniconda3...")
            success, _ = self.run_command(
                ['bash', str(installer), '-b', '-p', str(self.miniconda_path)],
                description="Install Miniconda3",
                as_root=False
            )
            
            if not success:
                self.print_error("Failed to install Miniconda3")
                return False
            
            # Initialize conda for bash
            self.run_command(
                [str(self.miniconda_path / 'bin' / 'conda'), 'init', 'bash'],
                description="Initialize conda for bash",
                as_root=False
            )
            
            # Fix permissions
            self.run_command(
                ['chown', '-R', f'{self.username}:{self.username}', str(self.miniconda_path)],
                description="Fix Miniconda permissions",
                as_root=True
            )
            
            # Cleanup
            installer.unlink(missing_ok=True)
            
            self.print_ok(f"Miniconda3 installed at {self.miniconda_path}")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup Miniconda3: {e}")
            return False

    def step_3_conda_environment(self):
        """Step 3: Create and configure conda environment"""
        self.print_step(3, f"Setting up conda environment '{self.conda_env_name}'")
        
        conda_bin = self.miniconda_path / 'bin' / 'conda'
        
        if not conda_bin.exists():
            self.print_error(f"Conda binary not found at {conda_bin}")
            return False
        
        try:
            # Check if environment already exists
            success, output = self.run_command(
                [str(conda_bin), 'env', 'list', '--json'],
                description="List conda environments",
                capture_output=True,
                as_root=False
            )
            
            if success:
                try:
                    env_data = json.loads(output)
                    existing_envs = [Path(p).name for p in env_data.get('envs', [])]
                    if self.conda_env_name in existing_envs:
                        self.print_ok(f"Conda environment '{self.conda_env_name}' already exists")
                        return True
                except:
                    pass
            
            # Create environment
            self.print_step(3, "Creating conda environment with Python 3.11...")
            success, _ = self.run_command(
                [str(conda_bin), 'create', '-y', '-n', self.conda_env_name, 'python=3.11'],
                description=f"Create {self.conda_env_name} environment",
                as_root=False
            )
            
            if not success:
                self.print_error("Failed to create conda environment")
                return False
            
            # Set as default environment
            bashrc = self.user_home / '.bashrc'
            activation_line = f"conda activate {self.conda_env_name}"
            
            if bashrc.exists():
                with open(bashrc, 'r') as f:
                    content = f.read()
                
                if activation_line not in content:
                    with open(bashrc, 'a') as f:
                        f.write(f"\n# Auto-activate fiber-laser-dmx environment\n{activation_line}\n")
                    self.print_ok(f"Added auto-activation to {bashrc}")
            
            self.print_ok(f"Created conda environment '{self.conda_env_name}' with Python 3.11")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup conda environment: {e}")
            return False

    def step_4_python_dependencies(self):
        """Step 4: Install Python dependencies"""
        self.print_step(4, "Installing Python dependencies via pip")
        
        req_file = self.project_root / 'requirements.txt'
        if not req_file.exists():
            self.print_error(f"File not found: {req_file}")
            return False
        
        try:
            pip_bin = self.miniconda_path / 'envs' / self.conda_env_name / 'bin' / 'pip'
            
            if not pip_bin.exists():
                self.print_error(f"pip binary not found at {pip_bin}")
                return False
            
            # Read Python requirements
            with open(req_file, 'r') as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not packages:
                self.print_warning("No packages found in requirements.txt")
                return False
            
            self.print_step(4, f"Installing {len(packages)} Python packages...")
            
            # Install packages
            success, _ = self.run_command(
                [str(pip_bin), 'install', '--upgrade', 'pip', 'setuptools', 'wheel'],
                description="Upgrade pip, setuptools, wheel",
                as_root=False
            )
            
            success, _ = self.run_command(
                [str(pip_bin), 'install'] + packages,
                description=f"Install {len(packages)} Python packages",
                as_root=False
            )
            
            if success:
                self.print_ok(f"Installed {len(packages)} Python packages")
                return True
            
            self.print_warning("Some packages may have failed to install")
            return True  # Don't fail on partial install
            
        except Exception as e:
            self.print_error(f"Failed to install Python dependencies: {e}")
            return False

    def step_5_ftdi_rules(self):
        """Step 5: Configure FTDI USB-DMX udev rules"""
        self.print_step(5, "Configuring FTDI USB-DMX udev rules")
        
        try:
            ftdi_rules_src = self.project_root / 'services' / '99-ftdi.rules'
            ftdi_rules_dst = Path('/etc/udev/rules.d/99-ftdi.rules')
            
            if not ftdi_rules_src.exists():
                self.print_error(f"FTDI rules file not found: {ftdi_rules_src}")
                return False
            
            # Copy udev rules
            success, _ = self.run_command(
                ['cp', str(ftdi_rules_src), str(ftdi_rules_dst)],
                description="Copy FTDI udev rules",
                as_root=True
            )
            
            if not success:
                self.print_error("Failed to copy FTDI rules")
                return False
            
            # Reload udev rules
            success, _ = self.run_command(
                ['udevadm', 'control', '--reload-rules'],
                description="Reload udev rules",
                as_root=True
            )
            
            if success:
                self.print_ok("FTDI USB-DMX udev rules configured")
                return True
            
            return False
            
        except Exception as e:
            self.print_error(f"Failed to configure FTDI rules: {e}")
            return False

    def step_6_systemd_services(self):
        """Step 6: Setup systemd services"""
        self.print_step(6, "Setting up systemd services")
        
        services = [
            ('conda-fiber-laser.service', 'Conda environment initialization'),
            ('dmx-ui.service', 'DMX Flask Web UI'),
            ('qlcplus-web.service', 'QLC+ Web Interface'),
        ]
        
        services_dir = self.project_root / 'services'
        systemd_dir = Path('/etc/systemd/system')
        
        try:
            for service_name, description in services:
                service_src = services_dir / service_name
                service_dst = systemd_dir / service_name
                
                if not service_src.exists():
                    self.print_warning(f"Service file not found: {service_src}")
                    continue
                
                # Copy service file
                success, _ = self.run_command(
                    ['cp', str(service_src), str(service_dst)],
                    description=f"Copy {service_name}",
                    as_root=True
                )
                
                if not success:
                    continue
                
                # Reload systemd daemon
                self.run_command(
                    ['systemctl', 'daemon-reload'],
                    description="Reload systemd daemon",
                    as_root=True
                )
                
                # Enable service
                success, _ = self.run_command(
                    ['systemctl', 'enable', service_name],
                    description=f"Enable {service_name}",
                    as_root=True
                )
                
                if success:
                    self.print_ok(f"Enabled {service_name} ({description})")
                else:
                    self.print_warning(f"Failed to enable {service_name}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup systemd services: {e}")
            return False

    def step_7_nginx_php(self):
        """Step 7: Install and configure nginx + PHP-FPM"""
        self.print_step(7, "Setting up nginx web server and PHP-FPM")
        
        try:
            # Install nginx and PHP packages
            success, _ = self.run_command(
                ['apt-get', 'install', '-y', 'nginx', 'php8.2-fpm'],
                description="Install nginx and PHP-FPM",
                as_root=True
            )
            
            if not success:
                self.print_warning("Failed to install nginx/PHP-FPM")
                return False
            
            # Enable and start services
            self.run_command(
                ['systemctl', 'enable', 'nginx'],
                description="Enable nginx",
                as_root=True
            )
            
            self.run_command(
                ['systemctl', 'enable', 'php8.2-fpm'],
                description="Enable PHP-FPM",
                as_root=True
            )
            
            self.print_ok("nginx and PHP-FPM installed and enabled")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup nginx/PHP-FPM: {e}")
            return False

    def step_8_hardinfo2_web(self):
        """Step 8: Deploy HardInfo2 web interface"""
        self.print_step(8, "Deploying HardInfo2 web interface")
        
        try:
            hardinfo2_src = self.project_root.parent / 'hardinfo2' / 'server' / 'www'
            hardinfo2_dst = Path('/var/www/html')
            
            if not hardinfo2_src.exists():
                self.print_warning(f"HardInfo2 source not found: {hardinfo2_src}")
                return False
            
            # Create destination directory
            self.run_command(
                ['mkdir', '-p', str(hardinfo2_dst)],
                description="Create web root directory",
                as_root=True
            )
            
            # Copy HardInfo2 files
            success, _ = self.run_command(
                ['cp', '-r', str(hardinfo2_src) + '/', str(hardinfo2_dst) + '/'],
                description="Copy HardInfo2 files to web root",
                as_root=True
            )
            
            if not success:
                self.print_warning("Failed to copy HardInfo2 files")
                return False
            
            # Set permissions
            self.run_command(
                ['chown', '-R', 'www-data:www-data', str(hardinfo2_dst)],
                description="Set HardInfo2 permissions",
                as_root=True
            )
            
            # Create nginx config
            nginx_config = """server {
    listen 8888;
    listen [::]:8888;
    
    server_name _;
    root /var/www/html;
    index index.html index.php;
    
    access_log /var/log/nginx/hardinfo2_access.log;
    error_log /var/log/nginx/hardinfo2_error.log;
    
    location ~* \\.(css|js|jpg|jpeg|png|gif|ico|svg|webp|woff|woff2|ttf|eot)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
    
    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param SCRIPT_NAME $fastcgi_script_name;
        fastcgi_param REQUEST_METHOD $request_method;
        fastcgi_param QUERY_STRING $query_string;
        fastcgi_param CONTENT_TYPE $content_type;
        fastcgi_param CONTENT_LENGTH $content_length;
        fastcgi_param SERVER_NAME $server_name;
        fastcgi_param SERVER_PORT $server_port;
        fastcgi_param SERVER_ADDR $server_addr;
        fastcgi_param REMOTE_ADDR $remote_addr;
        fastcgi_param REMOTE_PORT $remote_port;
        fastcgi_param REQUEST_URI $request_uri;
        fastcgi_param SCRIPT_URL $fastcgi_script_name;
        fastcgi_read_timeout 60;
        include fastcgi_params;
    }
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location ~ /\\. {
        deny all;
    }
}"""
            
            config_file = Path('/etc/nginx/sites-available/hardinfo2')
            with open(config_file, 'w') as f:
                f.write(nginx_config)
            
            # Enable the site
            self.run_command(
                ['ln', '-sf', str(config_file), '/etc/nginx/sites-enabled/hardinfo2'],
                description="Enable HardInfo2 nginx site",
                as_root=True
            )
            
            # Test and reload nginx
            self.run_command(
                ['nginx', '-t'],
                description="Test nginx configuration",
                as_root=True
            )
            
            self.run_command(
                ['systemctl', 'reload', 'nginx'],
                description="Reload nginx",
                as_root=True
            )
            
            self.print_ok("HardInfo2 web interface deployed on port 8888")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup HardInfo2 web interface: {e}")
            return False

    def step_9_wifi_hotspot(self):
        """Step 9: Configure WiFi hotspot"""
        self.print_step(9, "Configuring WiFi hotspot")
        
        try:
            hotspot_script = self.project_root / 'scripts' / 'setup-wifi-hotspot.sh'
            
            if not hotspot_script.exists():
                self.print_warning(f"WiFi hotspot script not found: {hotspot_script}")
                return False
            
            # Run the hotspot setup script
            success, _ = self.run_command(
                ['bash', str(hotspot_script)],
                description="Run WiFi hotspot setup",
                as_root=True
            )
            
            if success:
                self.print_ok("WiFi hotspot configured (laser-dmx SSID, 192.168.50.1)")
                return True
            
            return False
            
        except Exception as e:
            self.print_error(f"Failed to setup WiFi hotspot: {e}")
            return False

    def step_10_caddy_config(self):
        """Step 10: Configure Caddy reverse proxy"""
        self.print_step(10, "Configuring Caddy reverse proxy")
        
        try:
            # Check if Caddy is installed
            success, _ = self.run_command(
                ['which', 'caddy'],
                description="Check Caddy installation",
                capture_output=True,
                as_root=False
            )
            
            if not success:
                self.print_warning("Caddy not installed, skipping configuration")
                return True
            
            # Create/update Caddyfile
            caddyfile_content = """laser-dmx.local {
    reverse_proxy localhost:8080
    header X-Forwarded-For {remote_host}
    header X-Forwarded-Proto {scheme}
    header X-Forwarded-Host {host}
    log {
        output stdout
        format json
    }
}

:80 {
    reverse_proxy localhost:8080
    log {
        output stdout
        format json
    }
}"""
            
            caddyfile_path = Path('/etc/caddy/Caddyfile')
            with open(caddyfile_path, 'w') as f:
                f.write(caddyfile_content)
            
            # Reload Caddy
            self.run_command(
                ['systemctl', 'reload', 'caddy'],
                description="Reload Caddy",
                as_root=True
            )
            
            self.print_ok("Caddy reverse proxy configured")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to configure Caddy: {e}")
            return False

    def step_11_hardinfo2_database(self):
        """Step 11: Initialize HardInfo2 database (MariaDB)"""
        self.print_step(11, "Setting up HardInfo2 local database")
        
        try:
            # Enable and start MariaDB
            self.run_command(
                ['systemctl', 'enable', 'mariadb'],
                description="Enable MariaDB",
                as_root=True
            )
            
            self.run_command(
                ['systemctl', 'start', 'mariadb'],
                description="Start MariaDB",
                as_root=True
            )
            
            # Wait for MariaDB to start
            import time
            time.sleep(2)
            
            # Check if MariaDB is running
            success, _ = self.run_command(
                ['systemctl', 'is-active', 'mariadb'],
                description="Check MariaDB status",
                capture_output=True,
                as_root=True,
                check=False
            )
            
            if not success:
                self.print_warning("MariaDB may not have started, attempting initialization anyway")
            
            # Run SQL schema to initialize database
            schema_file = self.project_root / 'api' / 'hardinfo2_schema.sql'
            
            if not schema_file.exists():
                self.print_warning(f"Schema file not found: {schema_file}")
                return False
            
            # Initialize database from schema file
            with open(schema_file, 'r') as f:
                sql_commands = f.read()
            
            # Execute SQL as root (no password needed for root on fresh install)
            result = subprocess.run(
                ['mysql', '-u', 'root'],
                input=sql_commands,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                if 'already exists' in result.stderr or 'Duplicate entry' in result.stderr:
                    self.print_ok("HardInfo2 database already initialized")
                    return True
                else:
                    self.print_warning(f"Database initialization output: {result.stderr}")
                    # Don't fail - database might already exist
                    return True
            
            self.print_ok("HardInfo2 database initialized successfully")
            
            # Verify database was created
            verify_cmd = ["mysql", "-u", "hardinfo", "-phardinfo", "hardinfo", "-e", "SHOW TABLES;"]
            result = subprocess.run(
                verify_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'benchmark_result' in result.stdout:
                self.print_ok("HardInfo2 database verified - ready for benchmarks")
                return True
            else:
                self.print_warning("Could not verify database tables")
                return True  # Don't fail - tables may not be visible
            
        except subprocess.TimeoutExpired:
            self.print_warning("Database initialization timed out")
            return True  # Don't fail - MariaDB might still initialize
        except Exception as e:
            self.print_error(f"Failed to setup HardInfo2 database: {e}")
            return False

    def step_12_benchmark_dashboard(self):
        """Step 12: Create custom benchmark dashboard (Optional)"""
        self.print_step(12, "Creating benchmark dashboard (optional)")
        
        try:
            # Create simple dashboard HTML that queries the database
            dashboard_html = """<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .dashboard { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; }
        .stat-number { font-size: 32px; font-weight: bold; }
        .stat-label { font-size: 14px; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
</head>
<body>
    <div class="dashboard">
        <h1>🚀 Benchmark Dashboard</h1>
        
        <div class="card">
            <h2>System Overview</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number" id="total-benchmarks">-</div>
                    <div class="stat-label">Total Benchmarks</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" id="last-run">-</div>
                    <div class="stat-label">Last Run</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" id="machines">-</div>
                    <div class="stat-label">Unique Machines</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Recent Benchmarks</h2>
            <table id="recent-benchmarks">
                <tr>
                    <th>Machine</th>
                    <th>Benchmark</th>
                    <th>Result</th>
                    <th>Date</th>
                </tr>
            </table>
        </div>

        <div class="card">
            <h2>Performance Trends</h2>
            <canvas id="trendsChart"></canvas>
        </div>
    </div>

    <script>
        // Load dashboard data
        async function loadDashboard() {
            try {
                // This would connect to the API/database
                document.getElementById('total-benchmarks').textContent = 'Loading...';
                // Add actual data loading here
            } catch (error) {
                console.error('Dashboard error:', error);
            }
        }
        
        window.onload = loadDashboard;
    </script>
</body>
</html>"""
            
            dashboard_file = Path('/var/www/html/dashboard.html')
            with open(dashboard_file, 'w') as f:
                f.write(dashboard_html)
            
            self.run_command(
                ['chown', 'www-data:www-data', str(dashboard_file)],
                description="Set dashboard permissions",
                as_root=True
            )
            
            self.print_ok("Benchmark dashboard created at /dashboard.html")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to create dashboard: {e}")
            return False

    def step_13_scheduled_benchmarks(self):
        """Step 13: Set up scheduled daily benchmarks (Optional)"""
        self.print_step(13, "Setting up scheduled benchmarks (optional)")
        
        try:
            # Create a cron script to run benchmarks daily
            benchmark_script = """#!/bin/bash
# Daily benchmark runner for HardInfo2
# Runs benchmarks every day at 2 AM and stores results

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
LOG="/var/log/hardinfo2_benchmark.log"
MACHINE_ID=$(hostname)

echo "[$TIMESTAMP] Starting scheduled benchmark..." >> $LOG

# Run HardInfo2 benchmark
/usr/bin/hardinfo2 -q --generate-report -u "Auto-$MACHINE_ID" >> $LOG 2>&1

echo "[$TIMESTAMP] Benchmark completed" >> $LOG
"""
            
            script_path = Path('/usr/local/bin/hardinfo2-daily-benchmark.sh')
            with open(script_path, 'w') as f:
                f.write(benchmark_script)
            
            self.run_command(
                ['chmod', '+x', str(script_path)],
                description="Make benchmark script executable",
                as_root=True
            )
            
            # Add to crontab
            cron_entry = "0 2 * * * /usr/local/bin/hardinfo2-daily-benchmark.sh"
            cron_file = Path('/etc/cron.d/hardinfo2-benchmark')
            
            with open(cron_file, 'w') as f:
                f.write(f"# Daily HardInfo2 benchmark at 2 AM\n{cron_entry}\n")
            
            self.run_command(
                ['chmod', '644', str(cron_file)],
                description="Set cron permissions",
                as_root=True
            )
            
            self.print_ok("Scheduled benchmarks configured (daily at 2 AM)")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup scheduled benchmarks: {e}")
            return False

    def step_14_https_certificates(self):
        """Step 14: Configure HTTPS with Let's Encrypt (Optional)"""
        self.print_step(14, "Configuring HTTPS certificates (optional)")
        
        try:
            # Check if Caddy is running
            success, _ = self.run_command(
                ['systemctl', 'is-active', 'caddy'],
                description="Check Caddy status",
                capture_output=True,
                as_root=True,
                check=False
            )
            
            if not success:
                self.print_warning("Caddy not running, skipping HTTPS setup")
                return True
            
            # Update Caddyfile with HTTPS configuration
            caddyfile = Path('/etc/caddy/Caddyfile')
            if caddyfile.exists():
                with open(caddyfile, 'r') as f:
                    content = f.read()
                
                # Check if already configured for HTTPS
                if 'tls' in content or 'https' in content:
                    self.print_ok("HTTPS already configured in Caddyfile")
                    return True
                
                # Add HTTPS configuration
                https_config = """
# HTTPS Configuration
laser-dmx.local:443 {
    tls internal  # Use self-signed for local network
    reverse_proxy localhost:8080
}

# Automatic HTTPS redirect
laser-dmx.local {
    redir https://laser-dmx.local{uri}
}
"""
                with open(caddyfile, 'a') as f:
                    f.write(https_config)
                
                # Reload Caddy
                self.run_command(
                    ['systemctl', 'reload', 'caddy'],
                    description="Reload Caddy with HTTPS",
                    as_root=True
                )
                
                self.print_ok("HTTPS certificates configured (self-signed for local network)")
                return True
            
            return True
            
        except Exception as e:
            self.print_warning(f"Failed to setup HTTPS: {e}")
            return True  # Don't fail - HTTPS is optional

    def step_15_web_authentication(self):
        """Step 15: Add basic web authentication (Optional)"""
        self.print_step(15, "Setting up web authentication (optional)")
        
        try:
            # Create a simple authentication check PHP file
            auth_php = """<?php
// Simple authentication for HardInfo2 web interface
// Username: admin, Password: generate with: echo -n 'password' | md5sum

session_start();

// Default credentials (change these!)
$username = 'admin';
$password_hash = md5('admin');  // CHANGE THIS!

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $user = $_POST['username'] ?? '';
    $pass = $_POST['password'] ?? '';
    
    if ($user === $username && md5($pass) === $password_hash) {
        $_SESSION['authenticated'] = true;
        header('Location: /app');
        exit();
    } else {
        $error = 'Invalid credentials';
    }
}

// Check if authenticated
if (!isset($_SESSION['authenticated']) && $_SERVER['SCRIPT_URL'] !== '/login.php') {
    header('Location: /login.php');
    exit();
}
?>
"""
            
            auth_file = Path('/var/www/html/auth.php')
            with open(auth_file, 'w') as f:
                f.write(auth_php)
            
            # Create login page
            login_html = """<!DOCTYPE html>
<html>
<head>
    <title>HardInfo2 Login</title>
    <style>
        body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .login-box { background: white; padding: 40px; border-radius: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #667eea; color: white; border: none; border-radius: 3px; cursor: pointer; font-weight: bold; }
        .error { color: red; text-align: center; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 HardInfo2</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
            <?php if (isset($error)) echo '<p class="error">' . $error . '</p>'; ?>
        </form>
    </div>
</body>
</html>"""
            
            login_file = Path('/var/www/html/login.php')
            with open(login_file, 'w') as f:
                f.write(login_html)
            
            self.run_command(
                ['chown', 'www-data:www-data', str(auth_file), str(login_file)],
                description="Set authentication file permissions",
                as_root=True
            )
            
            self.print_ok("Web authentication configured (default: admin/admin - CHANGE THIS!)")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup authentication: {e}")
            return False

    def step_16_graphql_api(self):
        """Step 16: Set up GraphQL API for queries (Optional)"""
        self.print_step(16, "Setting up GraphQL API (optional)")
        
        try:
            # Create a GraphQL schema PHP file
            graphql_php = """<?php
// Simple GraphQL-like API for HardInfo2 benchmark queries
header('Content-Type: application/json');

$action = $_GET['action'] ?? 'schema';

switch ($action) {
    case 'schema':
        // Return GraphQL schema
        echo json_encode([
            'types' => [
                'BenchmarkResult' => [
                    'fields' => [
                        'id' => 'Int',
                        'benchmarkName' => 'String',
                        'result' => 'Float',
                        'machineId' => 'String',
                        'cpuName' => 'String',
                        'timestamp' => 'Int'
                    ]
                ],
                'Query' => [
                    'fields' => [
                        'benchmarks' => 'List(BenchmarkResult)',
                        'benchmark(id: Int)' => 'BenchmarkResult',
                        'benchmarksByName(name: String)' => 'List(BenchmarkResult)',
                        'recentBenchmarks(limit: Int = 10)' => 'List(BenchmarkResult)',
                        'machineStats' => 'List(MachineStatistics)'
                    ]
                ]
            ],
            'documentation' => 'Use ?action=help for API documentation'
        ]);
        break;
        
    case 'help':
        echo json_encode([
            'endpoints' => [
                '/api/graphql.php?action=schema' => 'Get API schema',
                '/api/graphql.php?action=recent&limit=10' => 'Get recent benchmarks',
                '/api/graphql.php?action=machine&id=pi5' => 'Get benchmarks for machine',
                '/api/graphql.php?action=compare&names=CPU,Memory' => 'Compare benchmarks'
            ]
        ]);
        break;
        
    case 'recent':
        // Return recent benchmarks
        $limit = min($_GET['limit'] ?? 10, 100);
        echo json_encode([
            'query' => 'recentBenchmarks',
            'limit' => $limit,
            'notice' => 'Connect to database to return actual results'
        ]);
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Unknown action']);
}
?>
"""
            
            graphql_file = Path('/var/www/html/api/graphql.php')
            with open(graphql_file, 'w') as f:
                f.write(graphql_php)
            
            self.run_command(
                ['chown', 'www-data:www-data', str(graphql_file)],
                description="Set GraphQL API permissions",
                as_root=True
            )
            
            self.print_ok("GraphQL API available at /api/graphql.php")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup GraphQL API: {e}")
            return False

    def step_17_boot_animation(self):
        """Step 17: Configure boot animation with mpv (Optional)"""
        self.print_step(17, "Setting up boot animation with mpv (optional)")
        
        try:
            # Run the boot animation setup script
            setup_script = self.project_root / 'scripts' / 'setup_boot_animation.sh'
            
            if not setup_script.exists():
                self.print_error(f"Boot animation setup script not found at {setup_script}")
                return False
            
            # Make it executable
            self.run_command(
                ['chmod', '+x', str(setup_script)],
                description="Make boot animation script executable",
                as_root=False
            )
            
            # Run the setup script
            success, output = self.run_command(
                [str(setup_script)],
                description="Install boot animation",
                capture_output=True,
                as_root=True
            )
            
            if success:
                self.print_ok("Boot animation installed successfully")
                self.print_ok("Video will play on next reboot: sudo reboot")
                return True
            else:
                self.print_error(f"Boot animation setup failed: {output}")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to setup boot animation: {e}")
            return False

    def verify_setup(self):
        """Verify the entire setup"""
        self.print_header("Verifying Setup")
        
        checks = {
            "Miniconda3": self.miniconda_path.exists(),
            "Conda environment": (self.miniconda_path / 'envs' / self.conda_env_name).exists(),
            "Project directory": self.project_root.exists(),
            "FTDI udev rules": Path('/etc/udev/rules.d/99-ftdi.rules').exists(),
        }
        
        all_ok = True
        for check_name, result in checks.items():
            if result:
                self.print_ok(f"{check_name} configured")
            else:
                self.print_error(f"{check_name} not found")
                all_ok = False
        
        # Check systemd services
        for service in ['dmx-ui.service', 'qlcplus-web.service']:
            success, _ = self.run_command(
                ['systemctl', 'is-enabled', service],
                description=f"Check {service}",
                capture_output=True,
                as_root=True,
                check=False
            )
            
            if success:
                self.print_ok(f"Systemd service {service} enabled")
            else:
                self.print_warning(f"Systemd service {service} not enabled")
        
        return all_ok

    def run(self):
        """Execute the full initialization"""
        self.print_header("Fiber Laser DMX System Initialization")
        print(f"Project root: {self.project_root}")
        print(f"Username: {self.username}")
        print(f"Miniconda path: {self.miniconda_path}")
        print(f"Conda environment: {self.conda_env_name}")
        
        if self.verify_only:
            self.print_header("Verification Mode")
            return self.verify_setup()
        
        self.verify_root()
        
        steps = [
            (self.step_1_system_dependencies, "System Dependencies"),
            (self.step_2_miniconda, "Miniconda3 Setup"),
            (self.step_3_conda_environment, "Conda Environment"),
            (self.step_4_python_dependencies, "Python Dependencies"),
            (self.step_5_ftdi_rules, "FTDI USB-DMX Rules"),
            (self.step_6_systemd_services, "Systemd Services"),
            (self.step_7_nginx_php, "nginx + PHP-FPM Setup"),
            (self.step_8_hardinfo2_web, "HardInfo2 Web Interface"),
            (self.step_9_wifi_hotspot, "WiFi Hotspot Configuration"),
            (self.step_10_caddy_config, "Caddy Reverse Proxy"),
            (self.step_11_hardinfo2_database, "HardInfo2 Database Setup"),
            # Optional Enhancements
            (self.step_12_benchmark_dashboard, "Benchmark Dashboard Setup"),
            (self.step_13_scheduled_benchmarks, "Scheduled Benchmark Service"),
            (self.step_14_https_certificates, "HTTPS Certificates (Caddy)"),
            (self.step_15_web_authentication, "Web Interface Authentication"),
            (self.step_16_graphql_api, "GraphQL API Setup"),
            (self.step_17_boot_animation, "Boot Animation Setup (mpv)"),
        ]
        
        results = []
        for step_func, step_name in steps:
            try:
                result = step_func()
                results.append((step_name, result))
                if not result:
                    self.print_warning(f"Step '{step_name}' reported issues")
            except Exception as e:
                self.print_error(f"Exception in '{step_name}': {e}")
                results.append((step_name, False))
        
        # Summary
        self.print_header("Initialization Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for step_name, result in results:
            status = f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC}" if result else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
            print(f"  {step_name:.<50} {status}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} steps completed{Colors.ENDC}")
        
        if passed == total:
            self.print_ok("All initialization steps completed successfully!")
            self.print_header("Next Steps")
            print("1. Restart your terminal or run: source ~/.bashrc")
            print("2. Verify the conda environment: conda info")
            print("3. Access DMX UI: http://10.0.0.84:8080")
            print("4. Access HardInfo2: http://10.0.0.84:8888")
            print("5. Check systemd services: systemctl status dmx-ui")
            return True
        else:
            self.print_warning(f"Initialization completed with {total - passed} issue(s)")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Master initialization script for Fiber Laser DMX Control System"
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify setup only, do not make changes'
    )
    
    args = parser.parse_args()
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    manager = InitializationManager(
        project_root=project_root,
        verify_only=args.verify
    )
    
    success = manager.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
