from app.modules.trackers.providers import extract_youtube_channel_id, parse_youtube_feed


def test_extract_youtube_channel_id_from_id_and_url() -> None:
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw"

    assert extract_youtube_channel_id(channel_id) == channel_id
    assert extract_youtube_channel_id(f"https://www.youtube.com/channel/{channel_id}") == channel_id
    assert (
        extract_youtube_channel_id(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        )
        == channel_id
    )


def test_parse_youtube_feed_returns_latest_entry() -> None:
    item = parse_youtube_feed(
        """
        <feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:yt="http://www.youtube.com/xml/schemas/2015">
          <entry>
            <yt:videoId>abc123</yt:videoId>
            <title>New club trailer</title>
            <link rel="alternate" href="https://www.youtube.com/watch?v=abc123" />
            <published>2026-05-10T12:00:00+00:00</published>
          </entry>
        </feed>
        """
    )

    assert item is not None
    assert item.external_id == "abc123"
    assert item.title == "New club trailer"
    assert item.url == "https://www.youtube.com/watch?v=abc123"
