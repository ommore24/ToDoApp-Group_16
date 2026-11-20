
async function api(url, options = {}) {
    const r = await fetch(url, {
        ...options,
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    if (r.status === 204) {
        return null;
    }

    const d = await r.json().catch(() => ({}));

    if (!r.ok) {
        throw Error(d.error || `Request failed (${r.status})`);
    }

    return d;
}


function globalError(msg) {
    const e = document.getElementById("globalError");

    if (e) {
        e.textContent = msg;
        e.classList.remove("hidden");
    }
}


function routeRole(u) {
    location.href = u.role === "admin"
        ? "/admin"
        : "/dashboard";
}


document.addEventListener("DOMContentLoaded", async () => {

    const nav = document.getElementById("sideNav");

    if (!nav) {
        return;
    }

    try {
        const response = await api("/api/auth/me");
        const u = response.user;

        const sideName = document.getElementById("sideName");
        const sideRole = document.getElementById("sideRole");
        const avatar = document.getElementById("avatar");

        if (sideName) sideName.textContent = u.name;
        if (sideRole) sideRole.textContent = u.role;

        if (avatar) {
            avatar.textContent = u.name
                ? u.name[0].toUpperCase()
                : "?";
        }

        const links = u.role === "admin"
            ? [
                ["/admin", "▦", "Admin dashboard"],
                ["/admin/users", "♙", "Manage users"],
                ["/tasks", "☷", "All tasks"]
            ]
            : [
                ["/dashboard", "▦", "Dashboard"],
                ["/tasks", "☷", "My tasks"]
            ];

        nav.innerHTML = links.map(x => `
            <a class="nav-link" href="${x[0]}">
                <span>${x[1]}</span>
                ${x[2]}
            </a>
        `).join("");

        nav.querySelectorAll("a").forEach(a => {
            if (a.getAttribute("href") === location.pathname) {
                a.classList.add("selected");
            }
        });

    } catch (e) {
        location.href = "/login";
        return;
    }

    document.getElementById("logoutButton")?.addEventListener(
        "click",
        async () => {
            try {
                await api("/api/auth/logout", {
                    method: "POST"
                });

                location.href = "/login";

            } catch (e) {
                globalError(e.message);
            }
        }
    );
});
