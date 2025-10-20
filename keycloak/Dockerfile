# ----------------------------------------------------------------------------------
# Stage 0: 🪶 UBI Micro Builder (The Curl Fix Stage)
# GOAL: Install the 'curl' binary and its dependencies into a temporary filesystem
#       for transfer to the minimal runtime image.
# ----------------------------------------------------------------------------------
FROM helix-keycloak-base:ubi9 AS ubi-micro-build 

# 🚨 IMPORTANT: The 'ubi9' tag must point to a UBI image with 'dnf' (e.g., ubi-minimal or ubi-micro with dnf pre-installed, or a UBI base you control).
# The use of 'dnf install --installroot' is mandatory for deploying to UBI-micro/Distroless.
USER root
RUN mkdir -p /mnt/rootfs && \
    # 💥 Install 'curl' and its shared library dependencies into the temporary '/mnt/rootfs' directory.
    #    We use --setopt install_weak_deps=false --nodocs to keep the transfer small.
    dnf install --installroot /mnt/rootfs curl --releasever 9 --setopt install_weak_deps=false --nodocs -y && \
    # 🧹 Clean up cache to prevent bloated builder stage size.
    dnf --installroot /mnt/rootfs clean all

# ----------------------------------------------------------------------------------
# Stage 1: 🧩 Keycloak Builder (Optimization Stage)
# GOAL: Run the Keycloak 'build' command to compile configuration into the final image,
#       which improves startup time significantly (KC_DB=postgres optimization).
# ----------------------------------------------------------------------------------
FROM helix-keycloak-base:24.0.4 AS builder 
# 🧠 Optimization: Pre-configure Keycloak for PostgreSQL persistence.
RUN /opt/keycloak/bin/kc.sh build --db=postgres

# # ----------------------------------------------------------------------------------
# # Stage 2: 🚀 Final Runtime Image (Minimal Appliance)
# # ----------------------------------------------------------------------------------
# FROM docker.io/keycloak/keycloak:24.0.4

# # ... (Previous COPY commands from ubi-micro-build and builder stages) ...
# COPY --from=ubi-micro-build /mnt/rootfs /
# COPY --from=builder /opt/keycloak/lib/quarkus/ /opt/keycloak/lib/quarkus/

# # ✅ FIX: Temporarily switch to root to run chown/chmod, then switch back to the secure user (1000).
# # The default user for this Keycloak image is 1000, but chown requires root privileges.
# USER root 
# RUN chown -R 1000:1000 /opt/keycloak && chmod -R g+rwX /opt/keycloak

# # 🚪 Keycloak runs as user 1000 by default (best practice)
# # This command ensures the container launches under the non-root user ID 1000.
# USER 1000

# ----------------------------------------------------------------------------------
# Stage 2: 🚀 Final Runtime Image (Minimal Appliance)
# ----------------------------------------------------------------------------------
FROM docker.io/keycloak/keycloak:24.0.4

# ... (Previous COPY commands from ubi-micro-build and builder stages) ...
COPY --from=ubi-micro-build /mnt/rootfs /
COPY --from=builder /opt/keycloak/lib/quarkus/ /opt/keycloak/lib/quarkus/

# 🥇 PLATINUM ADDITION: Copy the custom realm JSON into the auto-import directory.
# The source path is relative to the Dockerfile's build context (./config/helix-realm.json).
# The destination path is the Keycloak auto-import directory.
COPY ./config/helix-realm.json /opt/keycloak/data/import/

# ✅ FIX: Temporarily switch to root to run chown/chmod, then switch back to the secure user (1000).
# We need to ensure the copied realm file (and all other files) are owned by the non-root user 1000.
USER root 
RUN chown -R 1000:1000 /opt/keycloak && chmod -R g+rwX /opt/keycloak

# 🚪 Keycloak runs as user 1000 by default (best practice)
# This command ensures the container launches under the non-root user ID 1000.
USER 1000