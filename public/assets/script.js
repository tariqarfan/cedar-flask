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
form?.addEventListener('input', () => {
  status.textContent = '';
  validateConfirmation();
  if (form.elements.name) form.elements.name.setCustomValidity(form.elements.name.value.trim() ? '' : 'Please enter your name.');
});
form?.addEventListener('submit', event => {
  validateConfirmation();
  if (!form.reportValidity()) event.preventDefault();
});
document.querySelector('#forgot')?.addEventListener('click', () => {
  status.textContent = 'Password recovery is not available yet. Please contact your administrator.';
});
