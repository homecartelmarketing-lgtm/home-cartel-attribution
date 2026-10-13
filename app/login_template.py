"""
Login Page Template — matches dashboard aesthetic (dark #090d16,
Plus Jakarta Sans). Skills: frontend-design, web-design-guidelines.
Posts to /login, shows generic error, redirects to /dashboard on success.
"""


def get_login_html(error: str = "") -> str:
    err_block = ""
    if error:
        err_block = (
            '<div class="error" role="alert" aria-live="assertive">'
            + error.replace("<", "&lt;").replace(">", "&gt;")
            + "</div>"
        )
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in | Home Cartel Ad Attribution</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #090d16;
            --bg-card: #121929;
            --border: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-rose: #f43f5e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            -webkit-font-smoothing: antialiased;
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 36px 34px;
            width: 100%;
            max-width: 400px;
        }
        .brand { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
        .brand span { color: var(--text-muted); font-weight: 400; }
        .sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; }
        label { display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin: 14px 0 6px; }
        input {
            width: 100%;
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            padding: 11px 13px;
            font-size: 14px;
            font-family: inherit;
        }
        input:focus { outline: 2px solid var(--accent-blue); outline-offset: 1px; border-color: var(--accent-blue); }
        button {
            width: 100%;
            margin-top: 22px;
            background: var(--accent-blue);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            font-weight: 600;
            padding: 12px;
            cursor: pointer;
            font-family: inherit;
        }
        button:hover { filter: brightness(1.1); }
        button:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
        .error {
            background: rgba(244, 63, 94, 0.12);
            border: 1px solid rgba(244, 63, 94, 0.4);
            color: #fda4af;
            font-size: 13px;
            border-radius: 8px;
            padding: 10px 13px;
            margin-bottom: 6px;
        }
        .hint { margin-top: 18px; font-size: 12px; color: var(--text-muted); text-align: center; }
    </style>
</head>
<body>
    <main class="card">
        <div class="brand">Home Cartel <span>| Ad Attribution</span></div>
        <p class="sub">Sign in to view the attribution dashboard.</p>
""" + err_block + """
        <form method="post" action="/login" autocomplete="off">
            <label for="username">Username</label>
            <input id="username" name="username" type="text" required autocomplete="username" autofocus>
            <label for="password">Password</label>
            <input id="password" name="password" type="password" required autocomplete="current-password">
            <button type="submit">Sign in</button>
        </form>
        <p class="hint">Sessions expire after 12 hours.</p>
    </main>
</body>
</html>
"""
