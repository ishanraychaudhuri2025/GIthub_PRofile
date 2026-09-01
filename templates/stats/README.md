# Self-hosted GitHub Stats Template

This template follows the profile documents' recommended self-hosted `github-readme-stats` setup.

## 1. Fork

Fork [`anuraghazra/github-readme-stats`](https://github.com/anuraghazra/github-readme-stats) into your own GitHub account.

## 2. Deploy to Vercel

Create a free Vercel Hobby project and import the fork. Keep the normal build settings.

## 3. Add the token

Create a GitHub **classic** personal access token with the `repo` scope. The source documents specify no expiration and explicitly warn that the token must never be pasted into a public repository or chat. Put it only in Vercel as:

```text
PAT_1=<your-token>
```

See the companion `vercel.json` for a small runtime template.

## 4. Verify

After deployment, verify:

```text
https://YOUR-INSTANCE.vercel.app/api?username=ishanraychaudhuri2025&show_icons=true
```

## 5. README embed

```html
<div align="center">
  <img width="100%" src="https://streak-stats.demolab.com/?user=ishanraychaudhuri2025&hide_border=true&background=0A101F&stroke=22D3EE&ring=A78BFA&fire=10B981&currStreakLabel=22D3EE&sideLabels=94A3B8&currStreakNum=F8FAFC&sideNums=F8FAFC&dates=64748B&titleColor=22D3EE&card_width=1180" alt="streak" />
  <br />
  <img width="49%" src="https://YOUR-INSTANCE.vercel.app/api?username=ishanraychaudhuri2025&show_icons=true&count_private=true&include_all_commits=true&hide_rank=true&hide_border=true&title_color=22D3EE&icon_color=A78BFA&text_color=94A3B8&bg_color=0A101F&card_width=500" alt="stats" />
  <img width="49%" src="https://YOUR-INSTANCE.vercel.app/api/top-langs/?username=ishanraychaudhuri2025&layout=compact&langs_count=8&hide_border=true&title_color=22D3EE&text_color=94A3B8&bg_color=0A101F&card_width=500" alt="top languages" />
</div>
```

The documents recommend `hide_rank=true` because the rank is strongly affected by repository stars and followers rather than being a clean measure of coding ability. fileciteturn0file0L72-L74

## Notes

Stats can differ slightly from GitHub's native contribution totals because the source project can use different date windows and caching. Top languages measure detected code volume, so generated/template-heavy repositories can distort the result. fileciteturn0file0L193-L196
