# Deploy the Kinoquence showcase

Kinoquence's static showcase lives in `site/`. It is a static HTML/CSS/JavaScript site; it does not require a server-side application or a build step.

## Before enabling deployment

**Treat every file in `site/` as public.** GitHub Pages sites are publicly accessible on the internet even when the source repository is private and the account plan permits private-repository Pages. Do not enable deployment until the site, images, poster and video contain only material approved for public viewing.

GitHub Pages availability depends on the account plan. GitHub Free requires the source repository to be public; eligible paid plans can publish from private repositories. Check the current [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site#who-can-use-this-feature).

## Configure GitHub Pages

1. Open the repository's **Settings → Pages**.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Open **Settings → Secrets and variables → Actions → Variables**.
4. Create a repository variable named `PAGES_DEPLOY_ENABLED` with the value `true`.
5. Push a change to `site/**` on the default branch, or run **Deploy static showcase** manually from the Actions tab.

The included workflow deploys the contents of `site/` and uses the minimum GitHub token permissions required by the Pages deployment actions. When `PAGES_DEPLOY_ENABLED` is absent or not exactly `true`, the deployment job is skipped. This keeps CI clean while Pages is intentionally disabled.

## Verify a deployment

After a successful workflow run, open the Pages URL shown in the workflow's `github-pages` environment or in **Settings → Pages**. Check the home page, poster, video, stylesheet and JavaScript in a fresh browser session.

For a custom domain, configure the domain in **Settings → Pages** and follow GitHub's DNS and HTTPS guidance. A `CNAME` file alone does not configure the domain.

## References

- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
