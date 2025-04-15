import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from app.config import Config

class UpdateService:
    @staticmethod
    def check_for_updates():
        max_retries = 3
        initial_delay = 1

        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': Config.USER_AGENT
                }
                response = requests.get(Config.WIKI_PAGE_URL,
                                        headers=headers,
                                        timeout=10)

                if response.status_code == 429:
                    # Get retry-after header or use exponential backoff
                    delay = int(response.headers.get('Retry-After', initial_delay * (2 ** attempt)))
                    next_retry = datetime.now().replace(microsecond=0) + timedelta(seconds=delay)

                    if attempt == max_retries - 1:
                        return f"""
                            <div style='background-color: #fff0f0; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>
                                <strong>Too Many Requests</strong><br>
                                We've made too many requests to the server.<br>
                                Please try again at {next_retry.strftime('%I:%M:%S %p')}.
                            </div>
                        """

                    time.sleep(delay)
                    continue

                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find both Current Events and Recurring Events sections
                events_sections = [
                    ('Upcoming Content & Events', soup.find('div', id='Current_Events')),
                    ('Recurring Events', soup.find('div', id='Recurring_Events'))
                ]

                update_html = ""
                for section_title, section in events_sections:
                    if section:
                        # Get all countdown containers in this section
                        events_containers = section.find_next('div').find_all('div', class_='countdown-container')

                        if events_containers:
                            update_html += f"<h2>{section_title}</h2>"

                            for container in events_containers:
                                # Get event title
                                header = container.find('div', class_='countdown-header')
                                # Get countdown info
                                countdown_div = container.find('div', class_='countdown')
                                # Get event description
                                description = container.find('small')

                                if header and countdown_div:
                                    title = header.get_text().strip()

                                    # Handle both recurring and one-time events
                                    if 'data-type' in countdown_div.attrs and countdown_div['data-type'] == 'recurring':
                                        # Recurring event
                                        timestamp = int(countdown_div.get('data-timestamp', 0))
                                        duration = int(countdown_div.get('data-duration', 0))
                                        period = int(countdown_div.get('data-period', 0))
                                        offset = int(countdown_div.get('data-period-offset', 0))
                                        show_seconds = countdown_div.get('data-show-seconds', 'false') == 'true'

                                        bg_color = "#fff0e8"  # Orange-ish for recurring events
                                        countdown_text = f"Recurring event (every {period//3600} hours)"

                                    else:
                                        # One-time event
                                        timestamp = int(countdown_div.get('data-timestamp', 0))

                                        # Find if it's starting or ending
                                        prev_text = countdown_div.previous_sibling
                                        status_text = prev_text.strip() if prev_text else ""

                                        if timestamp > 1000000000000:  # If timestamp is in milliseconds
                                            event_time = datetime.fromtimestamp(timestamp/1000)
                                            time_str = event_time.strftime("%B %d, %Y at %I:%M %p")

                                            is_active = "Ends" in status_text
                                            bg_color = "#e8ffe8" if is_active else "#ffe8e8"
                                            countdown_text = f"{status_text} {time_str}"
                                        else:
                                            bg_color = "#f0f8ff"
                                            countdown_text = "Time not available"

                                    desc = description.get_text().strip() if description else ""
                                    active_class = ' active' if bg_color == "#e8ffe8" else ''
                                    title_attr = ' title="Click to launch Fisch"' if bg_color == "#e8ffe8" else ''

                                    update_html += f"""
                                        <div class="event-card{active_class}" style='background-color: {bg_color};'{title_attr}
                                            data-timestamp="{timestamp}"
                                            data-type="{'recurring' if 'data-type' in countdown_div.attrs else 'onetime'}"
                                            {f'data-duration="{duration}"' if 'data-type' in countdown_div.attrs else ''}
                                            {f'data-period="{period}"' if 'data-type' in countdown_div.attrs else ''}
                                            {f'data-offset="{offset}"' if 'data-type' in countdown_div.attrs else ''}
                                            {f'data-show-seconds="{str(show_seconds).lower()}"' if 'data-type' in countdown_div.attrs else ''}>
                                            <strong>{title}</strong><br>
                                            <span class="countdown-text" style='color: #666;'>{countdown_text}</span>
                                            <br><span class="date-text" style='color: #888; font-size: 0.9em;'></span>
                                            {f"<br><small>{desc}</small>" if desc else ""}
                                        </div>
                                    """

                return update_html if update_html else "<div>No events found. Check the website for more information.</div>"
            except requests.RequestException as e:
                return f"Error checking for updates: Connection error - {str(e)}"
            except (AttributeError, ValueError) as e:
                return f"Error checking for updates: Failed to parse update information - {str(e)}"
