document.querySelectorAll('.year').forEach(el => { el.textContent = new Date().getFullYear(); });
document.querySelectorAll('.reveal').forEach(button => {
  button.addEventListener('click', () => {
    const input = button.previousElementSibling;
    const visible = input.type === 'password';
    input.type = visible ? 'text' : 'password';
    button.textContent = visible ? 'Hide' : 'Show';
    button.setAttribute('aria-label', visible ? 'Hide password' : 'Show password');
    button.setAttribute('aria-pressed', String(visible));
  });
});
const form = document.querySelector('form');
const status = document.querySelector('.status');
const confirmation = document.querySelector('#confirm');
function validateConfirmation() {
  if (confirmation) confirmation.setCustomValidity(confirmation.value === form.elements.password.value ? '' : 'Passwords do not match.');
}
form.addEventListener('input', () => {
  status.textContent = '';
  validateConfirmation();
  if (form.elements.name) form.elements.name.setCustomValidity(form.elements.name.value.trim() ? '' : 'Please enter your name.');
});
form.addEventListener('submit', event => {
  event.preventDefault();
  validateConfirmation();
  if (!form.reportValidity()) return;
  status.textContent = form.dataset.mode === 'register'
    ? 'Your registration form is valid! This demo does not create an account.'
    : 'Your sign-in form is valid! Connect a backend to authenticate accounts.';
});
document.querySelector('#forgot')?.addEventListener('click', () => {
  status.textContent = 'Password recovery needs an authentication backend. No reset email has been sent.';
});
