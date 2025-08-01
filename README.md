# PyBit – Python C2 Framework

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-%40DarkBit-blue.svg)](https://t.me/DarkBitx)

**PyBit** is a lightweight, modular Command & Control (C2) framework written in Python. Designed for Red Team operations, threat emulation, and offensive security training, PyBit enables advanced adversary simulation with extensible transport layers (HTTP, TCP), task management, and beacon capabilities.

---

## 🚀 Features

- **Multi-Protocol Listeners**: HTTP & TCP listeners with dynamic routing and authentication.
- **Task Management**: Create, schedule, and track tasks per agent with in-memory store.
- **Persistent Shells**: Maintain interactive PowerShell or Bash shells across commands.
- **Encryption & TLS**: AES encryption at transport layer; optional HTTPS support for HTTP listener.
- **Modular Architecture**: Easily add new transports (e.g., WebSocket), auth methods, or agent profiles.
- **Logging & Auditing**: Built-in logging with configurable log levels and file output.
- **Agent Profiles**: Customize agent heartbeat, jitter, padding, and post/get URIs.

---

## 📦 Repository Structure

```text
PyBit/
├── LICENSE                # MIT License
├── README.md              # Project overview and instructions
├── config/                # Configuration schemas (JSON/YAML)
│   └── example_config.json
├── core/                  # Core modules and utilities
│   ├── agents/            # Agent handler and payload builders
│   ├── listener/          # Listener implementations (HTTP, TCP)
│   ├── transport/         # HTTPRequest, TCPRequest abstractions
│   ├── utils/             # Common functions, JSON persister, logger
│   └── taskmng.py         # Task management functions
├── payloads/              # Agent payload builders (stagers, beacons)
├── examples/              # Example workflows and configs
├── scripts/               # Deployment and helper scripts
└── docs/                  # Detailed documentation (TTPs, diagrams)
```

---

## 🛠 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/YourUser/PyBit.git
   cd PyBit
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure**

   - Copy `config/example_config.json` to `config/config.json`
   - Update listener IP/Port, TLS certs, agent profiles, and encryption key.

---

## ⚙️ Configuration

```json
{
  "teamserver": {
    "ip": "0.0.0.0",
    "port": "8000",
    "server_name": "PyBit-TeamServer",
    "auth": { "enabled": true, "method": "password", "password": "pybit" },
    "listener": {
      "http": { ... },
      "tcp": { ... }
    },
    "agent": { ... },
    "encryption": { "enabled": true, "method": "AES", "key": "<256-bit-key>" }
  }
}
```

See `docs/configuration.md` for full field descriptions.

---

## 🏃‍♂️ Usage

### Start TeamServer

```bash
python3 run_teamserver.py --config config/config.json
```

### Generate Agent Payloads

```bash
python3 payloads/generate.py --type http --output agent.py
```

### Interactive CLI

```bash
python3 pybit_cli.py
# Commands:
#   list       - list listeners
#   spawn      - start new listener
#   agents     - list connected agents
#   tasks      - list tasks
#   result     - fetch task results
#   exit       - quit
```

---

## 📖 Documentation

- **TTP Library**: `docs/ttp.md` – tactics, techniques, and procedures.
- **Architecture**: `docs/architecture.md` – module interactions and data flows.
- **API Reference**: `docs/api_reference.md` – classes, methods, and endpoints.

---

## 🤝 Contribution

Contributions, issues, and feature requests are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/XYZ`)
3. Commit your changes (`git commit -m 'Add XYZ'`)
4. Push to the branch (`git push origin feature/XYZ`)
5. Open a Pull Request

Please adhere to the code style and write tests for new functionality.

---

## 📜 License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## 📣 Connect

**Telegram**: [@DarkBitc](https://t.me/DarkBitc) – join our underground cybersecurity community.

**GitHub**: [https://github.com/YourUser/PyBit](https://github.com/YourUser/PyBit)

---

<p align="center">_Built with ☕ and Python_</p>
