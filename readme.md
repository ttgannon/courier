# courier

Welcome to Courier, an app that lets users get news their way. Using the News API (newsapi.org), users can set preferences about content, countries, and news organziations to scroll their curated feed for breaking news.

This was designed using Flask and Bootstrap.

# General Flow
Users begin by creating an account with a unique username and email, and an encrypted password. They are first taken to a page where they can select which countries they want to get headlines from, which then refines the news organizations they can select. With these preferences, a user sets their homepage view, which pulls breaking news headlines from the News API. 

# Features
Users can click on the Discover tab to find sources from other countries divided by theme; for example, they can view breaking news articles from the USA related to technology, or business, or health, and several other categories. 

Sometimes, the News API has access to a link to the story. If there is a link, the user will receive a link to follow to read the entire story.

Finally, users can edit their profile preferences from their settings to add new countries or news sources.

