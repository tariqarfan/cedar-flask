<?php require __DIR__ . '/includes/bootstrap.php'; handle_dashboard(); ?>
<!doctype html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Your account — Cedar</title><link rel="stylesheet" href="assets/style.css"></head>
<body class="dashboard-page">
  <header class="dashboard-header">
    <a class="brand" href="dashboard.php"><span class="logo">c.</span> cedar</a>
    <form method="post" action="logout.php">
      <input type="hidden" name="csrf_token" value="<?= e(csrf_token()) ?>">
      <button class="dashboard-signout" type="submit">Sign out →</button>
    </form>
  </header>
  <main class="dashboard-main">
    <span class="small-label">YOUR DASHBOARD</span>
    <section class="dashboard-welcome">
      <h1>Welcome, <?= e($user['name']) ?>.</h1>
      <p>It’s good to have you here. Wishing you a great day ahead!</p>
      <p class="dashboard-email">Signed in as <?= e($user['email']) ?></p>
    </section>
    <section class="dashboard-clock" aria-label="Current date and time">
      <span class="small-label">TODAY AT A GLANCE</span>
      <p id="current-date">Loading date…</p>
      <time id="current-time">Loading time…</time>
      <p class="dashboard-timezone" id="current-timezone">Your local time</p>
    </section>
  </main>
  <footer class="dashboard-footer"><span>© <span id="dashboard-year"></span> Cedar</span><span>A simpler way forward.</span></footer>
  <script defer src="assets/dashboard.js"></script>
</body>
</html>
