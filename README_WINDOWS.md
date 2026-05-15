# UnixPunks Hunter - Windows Setup Guide

## Prerequisites

1. **Python 3.7+** installed on your Windows machine
   - Download from: https://python.org/downloads/
   - During installation, check "Add Python to PATH"

## Quick Setup

1. **Download the files**:
   - `unixpunks_hunter_windows.py` - Main hunter script
   - `setup_windows.bat` - Setup script
   - `README_WINDOWS.md` - This guide

2. **Run setup**:
   ```cmd
   setup_windows.bat
   ```

3. **Run the hunter**:
   ```cmd
   python unixpunks_hunter_windows.py
   ```

## Manual Setup (Alternative)

If the batch file doesn't work, run these commands in PowerShell or Command Prompt:

```powershell
# Check Python
python --version

# Install required package
pip install requests

# Run the script
python unixpunks_hunter_windows.py
```

## Using Proxies (Optional)

If you have proxies, create a `proxies.txt` file in the same directory:

```
proxy1.example.com:8080:username:password
proxy2.example.com:8080:username:password
127.0.0.1:8888
```

Format options:
- With auth: `host:port:username:password`
- Without auth: `host:port`

## How to Use

1. **Start the script**: `python unixpunks_hunter_windows.py`
2. **Enter delay**: Time between attempts (default: 200ms)
3. **Enter wallet**: Your Ethereum wallet address (0x...)
4. **Press Enter**: Start hunting for mint codes
5. **Wait**: The script will try different timestamps
6. **Success**: When found, you'll get a mint code to use on the website

## Features

- ✅ Windows-optimized with better error handling
- ✅ Colorful emoji output for easy reading
- ✅ Proxy rotation support
- ✅ Rate limiting protection
- ✅ Progress tracking
- ✅ Graceful error handling
- ✅ User-friendly prompts

## Controls

- **Ctrl+C**: Stop the hunter at any time
- **Enter**: Confirm inputs and start hunting

## Troubleshooting

### "Python not found"
- Install Python from python.org
- Make sure "Add to PATH" was checked during installation
- Restart your command prompt

### "pip not found"
- Python should include pip automatically
- Try: `python -m pip install requests`

### Network errors
- Check your internet connection
- Try using proxies (create proxies.txt)
- Some networks may block the UnixPunks API

### Rate limiting
- The script handles this automatically
- Consider increasing delay between attempts
- Use multiple proxies to distribute requests

## Important Notes

⚠️ **Legal Compliance**: Make sure you comply with UnixPunks' terms of service
⚠️ **Rate Limiting**: Be respectful of the API, don't spam requests
⚠️ **Network**: Stable internet connection recommended
⚠️ **Wallet**: Double-check your wallet address is correct

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Make sure Python and requests are properly installed
3. Verify your internet connection
4. Try running with administrator privileges if needed

Good luck hunting! 🎯