# BFGMiner Setup Guide

Welcome to BFGMiner, the professional cryptocurrency mining platform. This comprehensive guide will help you install, configure, and run BFGMiner on your system.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Instructions](#installation-instructions)
   - [Windows](#windows-installation)
   - [macOS](#macos-installation)
   - [Linux](#linux-installation)
3. [Configuration](#configuration)
4. [Running BFGMiner](#running-bfgminer)
5. [Troubleshooting](#troubleshooting)
6. [Community Resources](#community-resources)
7. [Advanced Configuration](#advanced-configuration)

## System Requirements

### Minimum Requirements
- **CPU**: 64-bit processor (Intel/AMD)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 1GB free space
- **Network**: Stable internet connection
- **Operating System**: 
  - Windows 10/11 (64-bit)
  - macOS 10.14 or later
  - Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)

### Recommended Hardware
- **CPU**: Multi-core processor (4+ cores)
- **RAM**: 16GB or more
- **GPU**: NVIDIA/AMD graphics card (for GPU mining)
- **ASIC**: Compatible ASIC miners (see supported devices)

### Supported Mining Hardware
- **ASIC Miners**: Antminer series, Avalon, Block Erupter, and more
- **GPU**: NVIDIA GeForce, AMD Radeon series
- **FPGA**: Various FPGA development boards
- **USB Miners**: Block Erupter USB, GekkoScience, and compatible devices

## Installation Instructions

### Windows Installation

#### Prerequisites
1. **Install Visual Studio Redistributables**
   - Download and install Microsoft Visual C++ Redistributable for Visual Studio 2019
   - Available from Microsoft's official website

2. **Install Dependencies**
   - Download and install the latest Windows SDK
   - Install Git for Windows (optional, for source builds)

#### Installation Steps
1. **Extract the Archive**
   ```
   - Right-click on bfgminer-latest.zip
   - Select "Extract All..."
   - Choose your installation directory (e.g., C:\BFGMiner)
   ```

2. **Install Drivers**
   - For USB miners: Install WinUSB drivers using Zadig
   - For ASIC miners: Install manufacturer-specific drivers
   - For GPU mining: Install latest graphics drivers

3. **Configure Windows Defender**
   - Add BFGMiner folder to Windows Defender exclusions
   - This prevents false positive antivirus detections

4. **Test Installation**
   ```cmd
   cd C:\BFGMiner\bfgminer
   bfgminer.exe --help
   ```

### macOS Installation

#### Prerequisites
1. **Install Homebrew**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Dependencies**
   ```bash
   brew install autoconf automake libtool pkg-config curl libusb
   ```

#### Installation Steps
1. **Extract and Build**
   ```bash
   # Extract the downloaded archive
   unzip bfgminer-latest.zip
   cd bfgminer
   
   # Configure and build
   ./autogen.sh
   ./configure --enable-scrypt --enable-opencl
   make
   sudo make install
   ```

2. **Install USB Drivers**
   ```bash
   # For USB miners, install libusb
   brew install libusb-compat
   ```

3. **Test Installation**
   ```bash
   bfgminer --help
   ```

### Linux Installation

#### Ubuntu/Debian
1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install build-essential autoconf automake libtool pkg-config
   sudo apt install libcurl4-openssl-dev libjansson-dev libssl-dev libgmp-dev
   sudo apt install libusb-1.0-0-dev libudev-dev
   ```

2. **Build from Source**
   ```bash
   # Extract the archive
   unzip bfgminer-latest.zip
   cd bfgminer
   
   # Configure and build
   ./autogen.sh
   ./configure --enable-scrypt --enable-opencl --enable-cpumining
   make
   sudo make install
   ```

#### CentOS/RHEL/Fedora
1. **Install Dependencies**
   ```bash
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install curl-devel jansson-devel openssl-devel gmp-devel
   sudo yum install libusb1-devel systemd-devel
   
   # Fedora
   sudo dnf groupinstall "Development Tools"
   sudo dnf install curl-devel jansson-devel openssl-devel gmp-devel
   sudo dnf install libusb1-devel systemd-devel
   ```

2. **Build and Install**
   ```bash
   unzip bfgminer-latest.zip
   cd bfgminer
   ./autogen.sh
   ./configure --enable-scrypt --enable-opencl
   make
   sudo make install
   ```

## Configuration

### Basic Configuration

1. **Create Configuration File**
   Create a file named `bfgminer.conf` in your BFGMiner directory:
   ```json
   {
     "pools": [
       {
         "url": "stratum+tcp://pool.example.com:4444",
         "user": "your_wallet_address",
         "pass": "x"
       }
     ],
     "intensity": "d",
     "worksize": 256,
     "kernel": "scrypt",
     "lookup-gap": 2,
     "thread-concurrency": 8192,
     "shaders": 1792,
     "gpu-engine": "1000",
     "gpu-memclock": "1500",
     "gpu-powertune": 20,
     "temp-cutoff": 95,
     "temp-overheat": 85,
     "temp-target": 75,
     "auto-fan": true,
     "expiry": 120,
     "gpu-dyninterval": 7,
     "log": 5,
     "queue": 1,
     "retry-pause": 5,
     "scan-time": 60
   }
   ```

2. **Pool Configuration**
   - Replace `pool.example.com:4444` with your mining pool's address
   - Replace `your_wallet_address` with your cryptocurrency wallet address
   - Add backup pools for redundancy

### Hardware-Specific Configuration

#### ASIC Miners
```bash
# For Antminer S9
bfgminer -o stratum+tcp://pool.example.com:4444 -u wallet_address -p x -S antminer:all

# For Block Erupter USB
bfgminer -o stratum+tcp://pool.example.com:4444 -u wallet_address -p x -S erupter:all
```

#### GPU Mining
```bash
# For NVIDIA GPUs
bfgminer -o stratum+tcp://pool.example.com:4444 -u wallet_address -p x --scrypt -I d

# For AMD GPUs
bfgminer -o stratum+tcp://pool.example.com:4444 -u wallet_address -p x --scrypt -I 13
```

## Running BFGMiner

### Command Line Usage

#### Basic Commands
```bash
# Start mining with configuration file
bfgminer --config bfgminer.conf

# Start mining with command line parameters
bfgminer -o stratum+tcp://pool.example.com:4444 -u wallet_address -p x

# Scan for devices
bfgminer --scan-serial /dev/ttyUSB0

# List supported devices
bfgminer --help | grep -A 20 "Supported devices"
```

#### Advanced Options
```bash
# Enable verbose logging
bfgminer --config bfgminer.conf --verbose

# Set specific device
bfgminer -o pool_url -u user -p pass -S opencl:auto

# Benchmark mode
bfgminer --benchmark

# API access
bfgminer --config bfgminer.conf --api-listen --api-allow W:127.0.0.1
```

### Monitoring and Management

#### Runtime Hotkeys
- **[P]** - Pool management
- **[S]** - Settings
- **[D]** - Display options
- **[Q]** - Quit
- **[G]** - GPU management
- **[C]** - CPU management

#### Web Interface
Access the web interface at `http://localhost:4028` when API is enabled.

#### Log Files
- **Windows**: `%APPDATA%\BFGMiner\bfgminer.log`
- **macOS/Linux**: `~/.bfgminer/bfgminer.log`

## Troubleshooting

### Common Issues

#### Device Not Detected
1. **Check USB Connection**
   - Ensure device is properly connected
   - Try different USB ports
   - Check USB cable integrity

2. **Driver Issues**
   - Install/update device drivers
   - For Windows: Use Zadig to install WinUSB drivers
   - For Linux: Check udev rules

3. **Permission Issues (Linux)**
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout $USER
   
   # Create udev rule for USB miners
   echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666"' | sudo tee /etc/udev/rules.d/99-bfgminer.rules
   sudo udevadm control --reload-rules
   ```

#### Pool Connection Issues
1. **Check Pool Status**
   - Verify pool is online and accessible
   - Test connection with telnet: `telnet pool.example.com 4444`

2. **Firewall Settings**
   - Ensure mining ports are not blocked
   - Add BFGMiner to firewall exceptions

3. **Network Configuration**
   - Check proxy settings
   - Verify DNS resolution

#### Performance Issues
1. **Temperature Management**
   - Monitor GPU/ASIC temperatures
   - Improve cooling and ventilation
   - Reduce intensity if overheating

2. **Power Supply**
   - Ensure adequate power supply capacity
   - Check power connections
   - Monitor power consumption

3. **System Resources**
   - Close unnecessary applications
   - Increase virtual memory if needed
   - Monitor CPU and RAM usage

### Error Messages

#### "No devices detected"
- Check hardware connections
- Install proper drivers
- Verify device compatibility

#### "Pool connection failed"
- Verify pool URL and port
- Check internet connection
- Try alternative pools

#### "OpenCL platform not found"
- Install graphics drivers
- Install OpenCL runtime
- Check GPU compatibility

## Community Resources

### Official Resources
- **GitHub Repository**: https://github.com/luke-jr/bfgminer
- **Documentation**: https://github.com/luke-jr/bfgminer/blob/bfgminer/README
- **Release Notes**: Check GitHub releases for latest updates

### Community Forums
- **BitcoinTalk**: BFGMiner discussion threads
- **Reddit**: r/BitcoinMining, r/gpumining
- **Discord**: Mining community servers

### Mining Pools
Popular pools compatible with BFGMiner:
- **Slush Pool**: https://slushpool.com
- **F2Pool**: https://www.f2pool.com
- **Antpool**: https://www.antpool.com
- **ViaBTC**: https://www.viabtc.com

### Hardware Vendors
- **Bitmain**: Antminer series
- **Canaan**: Avalon miners
- **GekkoScience**: USB miners
- **Various**: FPGA development boards

## Advanced Configuration

### API Configuration
Enable API for remote monitoring:
```json
{
  "api-listen": true,
  "api-allow": "W:127.0.0.1,R:192.168.1.0/24",
  "api-port": 4028,
  "api-host": "0.0.0.0"
}
```

### Load Balancing
Configure multiple pools with priorities:
```json
{
  "pools": [
    {
      "url": "stratum+tcp://primary.pool.com:4444",
      "user": "wallet_address",
      "pass": "x",
      "priority": 0
    },
    {
      "url": "stratum+tcp://backup.pool.com:4444",
      "user": "wallet_address",
      "pass": "x",
      "priority": 1
    }
  ]
}
```

### Overclocking Settings
**Warning**: Overclocking can damage hardware. Proceed with caution.

```json
{
  "gpu-engine": "1100",
  "gpu-memclock": "1600",
  "gpu-powertune": 50,
  "gpu-vddc": 1.200
}
```

### Automated Startup

#### Windows Service
Create a Windows service to start BFGMiner automatically:
1. Use NSSM (Non-Sucking Service Manager)
2. Configure service parameters
3. Set to start automatically

#### Linux Systemd
Create a systemd service file:
```ini
[Unit]
Description=BFGMiner
After=network.target

[Service]
Type=simple
User=miner
ExecStart=/usr/local/bin/bfgminer --config /home/miner/bfgminer.conf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Security Considerations

1. **Network Security**
   - Use secure pool connections (SSL/TLS)
   - Implement firewall rules
   - Monitor network traffic

2. **System Security**
   - Run with minimal privileges
   - Keep system updated
   - Use antivirus software

3. **Wallet Security**
   - Use secure wallet addresses
   - Enable two-factor authentication on pools
   - Regular security audits

## Performance Optimization

### Hardware Optimization
1. **Cooling Solutions**
   - Adequate ventilation
   - Custom cooling systems
   - Temperature monitoring

2. **Power Efficiency**
   - Efficient power supplies
   - Power monitoring
   - Optimal voltage settings

3. **System Tuning**
   - Disable unnecessary services
   - Optimize system settings
   - Regular maintenance

### Software Optimization
1. **Driver Updates**
   - Latest graphics drivers
   - BIOS updates
   - Firmware updates

2. **Configuration Tuning**
   - Optimal intensity settings
   - Memory timing adjustments
   - Thread concurrency optimization

3. **Monitoring Tools**
   - GPU monitoring software
   - System monitoring tools
   - Mining pool statistics

## Conclusion

This guide provides comprehensive instructions for installing, configuring, and running BFGMiner. For additional support, consult the community resources and official documentation.

Remember to:
- Start with conservative settings
- Monitor temperatures and performance
- Keep software updated
- Follow safety guidelines
- Join the community for support

Happy mining!

---

**Disclaimer**: Cryptocurrency mining involves risks including hardware damage, electricity costs, and market volatility. Mine responsibly and at your own risk.

