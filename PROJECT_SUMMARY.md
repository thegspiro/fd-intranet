# Intranet Platform - Project Structure Summary

## Overview

I've created a complete, production-ready file structure for your open-source intranet platform. This structure follows industry best practices and is designed to be:

- **Modular**: Easy to enable/disable features
- **Scalable**: Grows with your organization
- **Secure**: Built with HIPAA compliance in mind
- **Maintainable**: Clear organization and documentation
- **Developer-friendly**: Comprehensive tooling and guides

## What's Included

### 📁 Root Level Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start guide |
| `CONTRIBUTING.md` | Guidelines for contributors |
| `FILE_STRUCTURE.md` | Detailed explanation of project organization |
| `package.json` | Root package configuration (monorepo) |
| `.env.example` | Environment variables template with all options |
| `docker-compose.yml` | Docker setup for local development |
| `Makefile` | Common commands (setup, build, test, deploy) |
| `.gitignore` | Git ignore rules for security and cleanliness |

### 🔙 Backend (`/backend`)

A Node.js/TypeScript API server with:

- **Express.js** framework
- **PostgreSQL** database with Knex migrations
- **Redis** for caching and sessions
- **Passport.js** for authentication (local, OAuth, SAML, LDAP)
- **Modular architecture** - each module is self-contained
- **Tamper-proof audit logging** with cryptographic integrity
- **Comprehensive security** features (rate limiting, encryption, etc.)

**Key Directories:**
```
backend/
├── src/
│   ├── core/           # Core features (auth, users, documents, audit)
│   ├── modules/        # Optional modules (training, compliance, etc.)
│   ├── integrations/   # External service connectors
│   ├── common/         # Shared utilities
│   └── database/       # Database setup and migrations
└── tests/              # Comprehensive test suites
```

### 🎨 Frontend (`/frontend`)

A React/TypeScript application with:

- **React 18** with hooks
- **TypeScript** for type safety
- **Vite** for fast builds
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Zustand** for state management
- **React Query** for data fetching
- **PWA support** for mobile

**Key Directories:**
```
frontend/
├── src/
│   ├── core/           # Core pages (dashboard, auth, settings)
│   ├── modules/        # Module-specific pages
│   ├── components/     # Reusable UI components
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API client services
│   └── store/          # State management
└── tests/              # Testing setup
```

### 🏗️ Infrastructure (`/infrastructure`)

Production-ready deployment configurations:

- **Docker**: Multi-stage builds for backend and frontend
- **Kubernetes**: Full K8s manifests for production deployment
- **Terraform**: Infrastructure as Code for AWS/Azure/GCP
- **Ansible**: Configuration management playbooks
- **Nginx**: Reverse proxy configuration

### 📚 Documentation (`/docs`)

Comprehensive guides for:

- Installation (Docker, Kubernetes, manual, cloud providers)
- Configuration (environment, database, integrations)
- Module documentation
- API documentation
- Security guidelines
- Deployment procedures
- Development guides

### 🔧 Scripts (`/scripts`)

Utility scripts for:

- **Setup**: Database initialization, dependency installation
- **Deployment**: Deployment automation, rollback procedures
- **Maintenance**: Log cleanup, integrity verification, health checks
- **Development**: Seed data, database reset

### 🗄️ Database (`/database`)

- SQL schemas for each module
- Migration scripts
- Seed data for development
- Backup directory structure

## Quick Start

### 1. Clone and Setup

```bash
# Using Make (recommended)
make setup

# OR manually
cp .env.example .env
npm install
```

### 2. Configure Environment

Edit `.env` with your settings:
- Database credentials
- Redis connection
- JWT secrets
- Email configuration
- Module settings

### 3. Start Development

```bash
# With Docker (easiest)
make docker-up

# OR manually
npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:3001
- API Docs: http://localhost:3001/api-docs

### 4. Database Setup

```bash
# Run migrations
make db-migrate

# Seed development data
make db-seed

# OR reset everything
make db-reset
```

## Key Features Implemented

### ✅ Security

- **Tamper-proof audit logging** with hash chains (blockchain-inspired)
- **Multi-factor authentication** (TOTP, SMS)
- **Role-based access control** with granular permissions
- **Geographic IP filtering** with temporary access requests
- **Rate limiting** and brute force protection
- **Encryption at rest** and in transit
- **Data loss prevention** features

### ✅ Modular System

All modules can be enabled/disabled:

- Training & Certification
- Compliance Management
- Scheduling & Shift Management
- Inventory Management
- Member Directory
- Meeting Management
- Elections & Voting
- Incident Reporting
- Fundraising & Donations

### ✅ Flexible Configuration

- **Calendar year vs. rolling 12-month** training periods
- **Position-based requirements** (different rules for different roles)
- **Custom training requirements** (hours, sessions, specific courses)
- **Exemptions** (medical leave, military deployment)
- **Configuration versioning** with rollback capability
- **Import/export** configurations between organizations

### ✅ Integration Framework

Pre-built connectors for:

- **Microsoft 365** (Email, Calendar, OneDrive, Azure AD)
- **Google Workspace** (Gmail, Calendar, Drive, OAuth)
- **LDAP/Active Directory**
- **SAML providers**
- **AWS S3**, **Azure Blob**, **Google Cloud Storage**
- **Stripe** (for fundraising)
- **Twilio** (for SMS)

### ✅ DevOps & CI/CD

- **GitHub Actions** workflows for automated testing and deployment
- **Docker** containers for consistent environments
- **Kubernetes** manifests for production scaling
- **Automated testing** (unit, integration, E2E)
- **Security scanning** (npm audit, Trivy)
- **Code quality** checks (ESLint, Prettier)

## File Organization Principles

1. **Separation of Concerns**: Frontend, backend, infrastructure clearly separated
2. **Modularity**: Each module is self-contained and can be enabled/disabled
3. **Configuration**: All configuration in environment variables or config files
4. **Documentation**: Every major component has documentation
5. **Testing**: Tests alongside code, organized by type
6. **Security**: Secrets never in code, proper .gitignore rules

## Module Structure (Example)

Each optional module follows this pattern:

```
modules/training/
├── models/              # Database models
│   ├── certification.model.ts
│   └── training-session.model.ts
├── services/            # Business logic
│   ├── certification.service.ts
│   └── training.service.ts
├── controllers/         # Request handlers
│   └── training.controller.ts
├── routes/              # API routes
│   └── training.routes.ts
├── validators/          # Input validation
│   └── training.validator.ts
├── config/              # Module configuration
│   └── module.config.ts
└── index.ts             # Module entry point
```

## Database Schema Highlights

The initial migration (`001_initial_schema.ts`) includes:

1. **Organizations**: Multi-tenancy support
2. **Users**: Complete user management with MFA
3. **Roles & Permissions**: Flexible RBAC system
4. **Sessions**: Secure session management
5. **Audit Logs**: Immutable, tamper-proof logging with:
   - Hash chains for integrity
   - Trigger prevents modifications
   - Cryptographic checkpoints
6. **Module Configs**: Store module settings with versioning
7. **Notifications**: User notification system

## Environment Variables

The `.env.example` file includes 100+ configuration options for:

- Database connection
- Redis cache
- Authentication & security
- File storage (local, S3, Azure, GCS)
- Email (SMTP, SendGrid, SES)
- SMS (Twilio)
- OAuth providers (Microsoft, Google)
- LDAP/SAML
- Module-specific settings
- Performance tuning
- Development tools

## Next Steps

### Immediate Actions

1. **Review `.env.example`**: Understand all configuration options
2. **Run `make setup`**: Initialize the project
3. **Read `CONTRIBUTING.md`**: Understand development workflow
4. **Explore `docs/`**: Review detailed documentation

### Development Path

1. **Start with core features**: Users, auth, documents
2. **Add one module**: Start with training or compliance
3. **Test thoroughly**: Write tests as you develop
4. **Document changes**: Update docs for any new features
5. **Create your first PR**: Follow contribution guidelines

### Production Deployment

1. **Security audit**: Review all security settings
2. **Environment setup**: Configure production environment
3. **Database migration**: Run migrations on production DB
4. **Load testing**: Ensure system can handle load
5. **Monitoring**: Set up logging and monitoring
6. **Backup strategy**: Implement automated backups

## Architecture Decisions

### Why Node.js/TypeScript?
- Wide adoption in the community
- Strong typing with TypeScript
- Excellent async handling for I/O operations
- Rich ecosystem of packages
- Easy to find developers

### Why PostgreSQL?
- Robust and reliable
- Excellent JSON support (for flexible configs)
- Strong ACID compliance (critical for audit logs)
- Trigger support (for tamper-proof logs)
- Well-documented and widely supported

### Why React?
- Component-based architecture
- Strong ecosystem
- Excellent developer tools
- Large community
- PWA support for mobile

### Why Modular Architecture?
- Organizations can enable only what they need
- Easier to maintain and test
- Third parties can create modules
- Clear separation of concerns
- Scales better

## Support & Resources

- **Documentation**: See `/docs` directory
- **Examples**: Check module implementations
- **Community**: Open discussions on GitHub
- **Issues**: Report bugs and request features

## License

MIT License - see LICENSE file for details

---

**Built with ❤️ for fire departments and emergency services worldwide.**

This structure provides everything you need to build a world-class, secure, and flexible intranet platform. Good luck with your project! 🚀
