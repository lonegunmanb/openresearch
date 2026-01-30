---
name: bypass-paywall
description: Bypass article paywalls using RemovePaywall.com and internet archives. Use when encountering paywalled content from news sites like WSJ, NYTimes, Bloomberg, Washington Post, Financial Times, The Atlantic, etc.
---

# Bypass Paywall

Access paywalled articles via internet archives.

## When to Use

- Page shows "Subscribe to continue reading"
- Content blocked by paywall or login wall
- News sites: WSJ, NYTimes, Bloomberg, WashPost, FT, The Atlantic, The Economist, Medium, etc.

## Workflow

### Option 1: RemovePaywall.com (Recommended)

Navigate directly to the search URL:
```
https://www.removepaywall.com/search?url=ARTICLE_URL
```

The page shows 4 options:
- **Option 1**: Google Cache
- **Option 2**: archive.is (newest)
- **Option 3**: archive.is (oldest)
- **Option 4**: Wayback Machine

Click each option button to try different archives.

### Option 2: Direct Archive Access

Try these archives directly:

1. **Archive.today**
   ```
   https://archive.is/newest/ARTICLE_URL
   ```

2. **Wayback Machine**
   ```
   https://web.archive.org/web/ARTICLE_URL
   ```

3. **Google Cache**
   ```
   https://webcache.googleusercontent.com/search?q=cache:ARTICLE_URL
   ```

## Handling Bot Detection

If archive sites show CAPTCHA or bot detection:
- Try a different archive option
- Wait briefly and retry
- Some archives may be temporarily unavailable

## Example

Original (paywalled):
```
https://www.wsj.com/articles/some-article-12345
```

Via RemovePaywall:
```
https://www.removepaywall.com/search?url=https://www.wsj.com/articles/some-article-12345
```

## Notes

- Works for "soft" paywalls that allow limited free access
- May not work for fully authenticated content
- Archive freshness varies; recent articles may not be archived yet
