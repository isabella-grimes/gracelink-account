# Deploying GraceERP Solution (with GraceERP Travel)

Step by step, for a fresh server (**A**) or the server you already run (**B**). Every command runs on the server as a user that can use Docker, unless it says *GitHub*.

You need:
- a server: Ubuntu 22.04/24.04, 4 vCPU, 8 GB RAM, 80 GB SSD, ports 80 and 443 open;
- DNS: `A erp.gracelinkgroup.com` and `A *.erp.gracelinkgroup.com` → the server IP;
- outbound internet from the server to `github.com`, `ghcr.io`, `pypi.org`, `gw-fatoora.zatca.gov.sa` and, for AI, `api.anthropic.com`.

## 0. GitHub: build the image (once, then weekly by itself)

The travel app's code repository (`isabella-grimes/grace-accounts`; not to be confused with the `grace-accounts` image package) is public, so the build needs no token.

1. **Build the image:** *GitHub* → `gracelink-account` → *Actions* → *Build image* → *Run workflow*, branch `platform`. It takes 15–25 minutes and publishes `ghcr.io/isabella-grimes/grace-accounts:16`. It also rebuilds every Sunday by itself.
2. **Is the image public or private?** *GitHub* → your avatar → *Your profile* → *Packages* → `grace-accounts`.
   - **Public:** the server pulls it without logging in.
   - **Private:** the server logs in once. Create a classic token (*Settings* → *Developer settings* → *Personal access tokens* → *Tokens (classic)*) with only the **`read:packages`** scope. GitHub's registry accepts only classic tokens. You'll use it in step A3/B2.

If you ever make the travel repository private again: mark it `"private": true` in `apps.json`, add a read-only token as the Actions secret `GRACE_REPO_TOKEN` (or in `.env` for `build.sh`), and make the image private too. The build uses the token only to clone; it never reaches the image.

## A. Fresh server

**A1. Docker**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER     # then log out and back in
docker compose version            # must print v2.x
```

**A2. Get the kit**
```bash
sudo git clone --branch platform https://github.com/isabella-grimes/gracelink-account /opt/grace-platform
sudo chown -R $USER /opt/grace-platform
cd /opt/grace-platform
./scripts/install.sh              # first run only creates .env with a generated DB password
```

**A3. Settings**: `nano .env`
```
PLATFORM_DOMAIN=erp.gracelinkgroup.com
LETSENCRYPT_EMAIL=<your email>
SUPPORT_URL=<your WhatsApp link or mailto:>
GRACE_IMAGE=ghcr.io/isabella-grimes/grace-accounts
PULL_POLICY=always
ANTHROPIC_API_KEY=<optional: the GraceLink key for Ask GRACE>
```
If the image is private (step 0.2), log in to the registry once, with the classic token as the password:
```bash
docker login ghcr.io -u isabella-grimes
```
*(Building on the server instead of GitHub: leave `GRACE_IMAGE=grace-accounts` and `PULL_POLICY=missing`. Then A4 builds the image here, in 10–20 minutes.)*

**A4. Start**
```bash
./scripts/install.sh              # pulls (or builds) the image and starts everything
docker compose --project-name grace ps      # all services "running"; "configurator" exits by design
docker compose --project-name grace exec backend ls apps   # must list grace_travel
```

**A5. Nightly backups**: `crontab -e`
```
0 2 * * * cd /opt/grace-platform && ./scripts/backup.sh >> backups/backup.log 2>&1
```
Copy `backups/` off the server too (rclone to Backblaze/S3). ZATCA requires invoices to be kept for years.

Continue with **C**.

## B. The server you already run

**B1. Get the new kit** (your `.env`, tenants and backups are untouched)
```bash
cd /opt/grace-platform
git pull                          # branch platform
```

**B2. Settings**: `nano .env`, add:
```
ANTHROPIC_API_KEY=<optional>
```
- **If you pull from GitHub** (`GRACE_IMAGE=ghcr.io/...`): do step 0. If the image is private, run `docker login ghcr.io -u isabella-grimes` (classic `read:packages` token).
- **If you build on the server** (`GRACE_IMAGE=grace-accounts`): nothing to add.

`.env.example` now defaults to `erp.gracelinkgroup.com`. Changing `PLATFORM_DOMAIN` in your `.env` only names **new** tenants; existing ones keep their address.

**B3. Update**
```bash
./scripts/update.sh               # backs up every tenant, pulls/builds, restarts, migrates all
docker compose --project-name grace exec backend ls apps   # must list grace_travel
```
If a tenant fails to migrate, the script names it and stops. Its backup is in `backups/<date>/`; see *Rolling back*.

## C. Travel agencies

**C1. A new agency**
```bash
./scripts/new-tenant.sh skyways --company "Sky Ways Travel" --email owner@skyways.sa --name "Sara Ali" --plan basic --travel
```
It prints the URL (`https://skyways.erp.gracelinkgroup.com`) and the owner's password.

**An existing customer becomes an agency:**
```bash
./scripts/enable-travel.sh acme   # backs up acme first
```

**C2. In the tenant** (log in as the owner, or as Administrator from `tenants/<site>.txt`):
1. **Travel Settings** → **Set Up Company** → **Create Suggested Accounts** → pick the company → *Run*.
2. **Set Up Company** → **Set Up Default VAT** → pick the company and its VAT account (e.g. *VAT 15%*) → *Run*.
3. **Set Up Company** → **Check Setup**: fix anything it lists until it says **Ready to issue tickets**. *Before going live* lists the ZATCA points.
4. **Customers:** business customers need their **VAT Registration Number** (the ZATCA field) and a full default address: building number (4 digits), district, city and postal code (5 digits). Walk-in customers need neither.

**C3. ZATCA e-invoicing** (per tenant, in **ZATCA Business Settings**):
1. Fill in the seller name, VAT number, address, *CRN* in the seller IDs, *Company Unit Serial*, and *Type of Business Transactions* (usually *Let the system decide (both)*); *Sync with ZATCA*: **Live**.
2. *CLI Setup*: **Automatic** → **Setup ZATCA CLI**. This downloads the ZATCA CLI and the Java 11 runtime it needs (don't point it at a newer system Java: Java 16 and later can't check ZATCA's signatures).
3. *Fatoora Server*: **Simulation** first. Get an OTP from the Fatoora simulation portal → **Create CSR** / onboard with it → **Perform Compliance Checks** (choose a walk-in customer, a business customer, the item *TRV-SVC-FEE* and the tax category *VAT 15%*) → **Get Production CSID** with a new OTP.
4. Issue a test ticket: open its Sales Invoice; the ZATCA status should be *Accepted* (cleared or reported) and the travel print shows the QR code.
5. When it works, repeat 3 on **Production** with an OTP from `fatoora.zatca.gov.sa`.

**C4. Ask GRACE (optional):** with `ANTHROPIC_API_KEY` in `.env`, the tenant's administrator opens **Grace AI Settings**, ticks *Use AI* and sets the monthly and daily token limits. Ask GRACE is then on the Travel Back Office workspace.

## Keeping it up to date

- **New travel or accounting features:** the image is rebuilt every Sunday. For a release in between: *GitHub* → *Actions* → *Build image* → *Run workflow*.
- **Then on the server:** `./scripts/update.sh`.

## Rolling back

- **Previous image:** every GitHub build is also tagged `16-<run number>` (see *Actions* → *Build image*). Set `GRACE_TAG=16-<previous number>` in `.env`, then run:
  ```bash
  docker compose --project-name grace --env-file .env -f compose.yaml up -d
  ```
  Set `GRACE_TAG=16` again for the next update.
- **A tenant's data:**
  ```bash
  ./scripts/restore-tenant.sh acme backups/<date>/<site>
  ```

## If something goes wrong

| Symptom | Fix |
|---|---|
| Build fails: *"…grace-accounts is a private repository. Set GRACE_REPO_TOKEN…"* | The travel repository is marked private in `apps.json`: add the token (see the end of step 0), or remove the mark if the repository is public. |
| Build fails: *"No such file or directory: …/apps/G/setup.py"*, or *"bench can't install a repository whose name contains a dot"* | An app's repository name has a dot (bench cuts the name there). Rename the repository and update `apps.json`. |
| Build fails cloning `isabella-grimes/grace-accounts` (*Authentication failed* / *not found*) | The repository was made private again: see the end of step 0. |
| `dc pull` / `install.sh`: *denied* or *unauthorized* from ghcr.io | `docker login ghcr.io -u isabella-grimes` with a classic token with `read:packages`. |
| `new-tenant.sh --travel`: *This image has no grace_travel* | The image predates the travel app: rebuild (step 0.3), then `./scripts/update.sh`. |
| A ticket stops: *ZATCA clears standard invoices only with the customer's full address* | Complete the customer's default address (C2.4). |
| ZATCA Integration Log: *Could not find a suitable TLS CA certificate bundle* | The containers can't reach the internet with valid certificates: check the server's outbound HTTPS. |
| Invoice validation: *Curve not supported: secp256k1* | The CLI runs on a Java newer than 11: run *Setup ZATCA CLI* (Automatic) again and clear *Java Home*. |
| Logs | `docker compose --project-name grace logs -f backend queue-short queue-long scheduler` |
