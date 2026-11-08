const button = document.getElementById('copy-install');
const status = document.getElementById('copy-status');
if (button) {
  button.addEventListener('click', async () => {
    const snippet = 'python -m pip install -e .\nkinoquence doctor\nkinoquence new projects/my-short\nkinoquence validate projects/my-short\nkinoquence audio projects/my-short\nkinoquence captions projects/my-short';
    try {
      await navigator.clipboard.writeText(snippet);
      status.textContent = 'Commands copied.';
    } catch {
      status.textContent = 'Clipboard access is blocked here. Select and copy the commands manually.';
    }
  });
}
