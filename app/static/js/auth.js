document.addEventListener("DOMContentLoaded", () => {
    const lf = document.getElementById("loginForm");
    const rf = document.getElementById("registerForm");
    const err = document.getElementById("authError");

    async function send(url, payload) {
        if (err) {
            err.classList.add("hidden");
        }
        try {
            const d = await api(url, {
                method: "POST",
                body: JSON.stringify(payload)
            });
            routeRole(d.user);
        } catch (e) {
            if (err) {
                err.textContent = e.message;
                err.classList.remove("hidden");
            }
        }
    }

    lf?.addEventListener("submit", (e) => {
        e.preventDefault();
        send("/api/auth/login", {
            email: document.getElementById("email").value.trim(),
            password: document.getElementById("password").value
        });
    });

    rf?.addEventListener("submit", (e) => {
        e.preventDefault();
        const password = document.getElementById("password").value;
        const confirm = document.getElementById("confirmPassword")?.value;

        if (confirm !== undefined && password !== confirm) {
            if (err) {
                err.textContent = "Passwords do not match";
                err.classList.remove("hidden");
            }
            return;
        }

        send("/api/auth/register", {
            name: document.getElementById("name").value.trim(),
            email: document.getElementById("email").value.trim(),
            password
        });
    });
});