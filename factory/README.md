# Software Factory

Automated assembly line for provisioning LAMP stack projects at scale.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOFTWARE FACTORY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT                  PROCESS                   OUTPUT         │
│  ─────                  ───────                   ──────         │
│                                                                  │
│  batch.yaml ──▶ [Factory Controller] ──▶ 10 Live Projects       │
│  (10 specs)         │                                           │
│                     ├── Provision Servers (parallel)            │
│                     ├── Configure DNS                           │
│                     ├── Install LAMP Stack                      │
│                     ├── Create Databases                        │
│                     ├── Deploy Applications                     │
│                     ├── Setup SSL                               │
│                     └── Health Checks                           │
│                                                                  │
│  TIME: ~17 minutes automated + ~10 minutes human review         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
cd factory
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp skyvern/.env.example skyvern/.env

# Edit with your API keys
nano skyvern/.env
```

Required keys:
- `DIGITALOCEAN_API_KEY` - For server provisioning
- `CLOUDFLARE_API_KEY` - For DNS management
- `CLOUDFLARE_ZONE_ID` - Your domain's zone ID
- `ANTHROPIC_API_KEY` - For Skyvern AI reasoning

### 3. Start Skyvern (Optional - for browser automation)

```bash
cd skyvern
chmod +x start.sh
./start.sh
```

### 4. Create a Batch

```bash
cp batches/batch-template.yaml batches/batch-001.yaml
nano batches/batch-001.yaml  # Edit project details
```

### 5. Run the Factory

```bash
# Dry run first
python scripts/factory_controller.py batches/batch-001.yaml --dry-run

# Actually run it
python scripts/factory_controller.py batches/batch-001.yaml
```

## Directory Structure

```
factory/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── skyvern/                     # Skyvern browser agent
│   ├── docker-compose.yml       # Docker setup
│   ├── .env.example            # Config template
│   ├── start.sh                # Startup script
│   ├── workflows/              # Saved workflows
│   └── recordings/             # Browser recordings
├── scripts/                     # Factory scripts
│   └── factory_controller.py   # Main orchestrator
├── batches/                     # Batch definitions
│   └── batch-template.yaml     # Template to copy
├── templates/                   # Server setup scripts
└── mcp-config.json             # MCP server config
```

## Batch File Format

```yaml
batch_id: "batch-001"
created: "2024-12-13"

projects:
  - id: "project-001"
    name: "my-app"
    domain: "myapp.yourdomain.com"
    client: "Client Name"
    server_size: "s-1vcpu-1gb"  # Optional
    region: "nyc3"               # Optional
```

## Server Sizes (DigitalOcean)

| Size | RAM | Price | Use Case |
|------|-----|-------|----------|
| s-1vcpu-512mb-10gb | 512MB | $4/mo | Minimal |
| s-1vcpu-1gb | 1GB | $6/mo | Starter (default) |
| s-1vcpu-2gb | 2GB | $12/mo | Small |
| s-2vcpu-4gb | 4GB | $24/mo | Medium |
| s-4vcpu-8gb | 8GB | $48/mo | Large |

## Regions

| Code | Location |
|------|----------|
| nyc3 | New York (default) |
| sfo3 | San Francisco |
| lon1 | London |
| fra1 | Frankfurt |
| ams3 | Amsterdam |
| sgp1 | Singapore |
| tor1 | Toronto |
| blr1 | Bangalore |

## MCP Integration

The factory integrates with Claude Code via MCP. Add to your MCP config:

```json
{
  "mcpServers": {
    "skyvern": {
      "command": "npx",
      "args": ["-y", "@anthropic/skyvern-mcp-server"],
      "env": {
        "SKYVERN_API_URL": "http://localhost:8000",
        "SKYVERN_API_KEY": "your-key"
      }
    }
  }
}
```

## Skyvern Workflows

Pre-built workflows for common tasks:

### DigitalOcean Console (when API isn't enough)
```yaml
name: do-create-droplet
url: https://cloud.digitalocean.com/droplets/new
steps:
  - action: fill
    selector: "#droplet-name"
    value: "{{project_name}}"
  - action: click
    selector: "[data-testid='create-droplet-btn']"
```

### Doppler Setup
```yaml
name: doppler-create-project
url: https://dashboard.doppler.com
steps:
  - action: click
    text: "New Project"
  - action: fill
    selector: "#project-name"
    value: "{{project_id}}"
```

## Human Checkpoints

After automation completes, you need to:

1. **Review batch report** (2 min)
2. **Verify SMTP** - Send test email from each project
3. **Add Stripe keys** - If payment processing needed
4. **Change admin passwords** - Before client handoff

## Costs

For a batch of 10 projects:

| Item | Cost |
|------|------|
| 10 Droplets ($6 each) | $60/month |
| DNS (Cloudflare) | Free |
| SSL (Let's Encrypt) | Free |
| Doppler (5 projects) | Free |
| Doppler (unlimited) | $20/month |
| **Total** | **$60-80/month** |

## Troubleshooting

### Server provisioning fails
- Check DigitalOcean API key
- Verify account has payment method
- Check SSH key is added to account

### DNS not working
- Verify Cloudflare Zone ID
- Check domain is active in Cloudflare
- Wait 5 minutes for propagation

### SSL fails
- DNS must propagate first (wait 5-10 min)
- Re-run SSL step manually:
  ```bash
  ssh root@IP "certbot --apache -d domain.com"
  ```

### SSH connection refused
- Server needs ~60 seconds to boot
- Verify SSH key matches what's on DigitalOcean
- Check firewall allows port 22

## License

Internal use only.
