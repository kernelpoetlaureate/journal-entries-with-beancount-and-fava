# Quick Commands Reference

## 🚀 First Time Setup
```bash
# In WSL
cd ~
chmod +x setup.sh
./setup.sh
```

## 📅 Daily Usage
```bash
# In WSL
cd ~
./start-beancount.sh
```

## 🛠️ Useful Commands

### Validate your ledger
```bash
bean-check my-ledger.beancount
```

### Format your ledger
```bash
bean-format my-ledger.beancount > formatted-ledger.beancount
```

### Start Fava on different port
```bash
fava my-ledger.beancount --port 5001
```

### Check Beancount version
```bash
python -c "import beancount; print(beancount.__version__)"
```

### Backup your ledger
```bash
cp my-ledger.beancount my-ledger-backup-$(date +%Y%m%d).beancount
```

## 🎯 Windows Users
- **Setup**: Double-click `setup.bat`
- **Daily use**: Double-click `start-beancount.bat`
- **Edit files**: Use VS Code or any text editor