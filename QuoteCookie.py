import sys
import random
import requests
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget, QFontDialog, QColorDialog, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap, QPalette, QBrush

# Local list of motivational quotes
local_quotes = [
    "Believe in yourself and all that you are.",
    "The only limit to our realization of tomorrow is our doubts of today.",
    "You are braver than you believe, stronger than you seem, and smarter than you think.",
    "Do what you can, with what you have, where you are.",
    "Act as if what you do makes a difference. It does.",
    "The best way to predict the future is to create it.",
    "Happiness is not something ready-made. It comes from your own actions.",
    "With the new day comes new strength and new thoughts."
]

# Function to fetch a random quote from ZenQuotes API
def fetch_online_quote():
    try:
        print("Fetching quote from ZenQuotes API...")
        response = requests.get("https://zenquotes.io/api/random", timeout=5)  # 5s timeout
        if response.status_code == 200:
            quote_data = response.json()
            return quote_data[0]["q"]
        else:
            print(f"API returned an error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from API: {e}")
    return None

# Worker thread for loading and resizing images to prevent freezing
class BackgroundWorker(QThread):
    image_loaded = pyqtSignal(QPixmap)  # Signal to notify the main thread

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path

    def run(self):
        pixmap = QPixmap(self.image_path)
        scaled_pixmap = pixmap.scaled(self.parent().size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.image_loaded.emit(scaled_pixmap)  # Emit signal with the resized image

# Main application class
class QuoteCookieApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("Quote Cookie")
        self.setGeometry(100, 100, 400, 200)

        # Create layout and widgets
        layout = QVBoxLayout()

        # Quote label, text will wrap and align
        self.quote_label = QLabel(self.get_quote(), self)
        self.quote_label.setWordWrap(True)
        self.quote_label.setAlignment(Qt.AlignCenter)
        self.quote_label.setStyleSheet("font-size: 16px; padding: 20px; text-align: center;")
        layout.addWidget(self.quote_label)

        # Add a button to show a new quote
        self.new_quote_button = QPushButton("Get a New Quote", self)
        self.new_quote_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.new_quote_button.clicked.connect(self.show_new_quote)
        layout.addWidget(self.new_quote_button)

        # Add a button to choose a custom font
        self.choose_font_button = QPushButton("Choose Font", self)
        self.choose_font_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.choose_font_button.clicked.connect(self.choose_font)
        layout.addWidget(self.choose_font_button)

        # Add a button to choose background color
        self.choose_color_button = QPushButton("Choose Background Color", self)
        self.choose_color_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.choose_color_button.clicked.connect(self.choose_background_color)
        layout.addWidget(self.choose_color_button)

        # Add a button to choose background image
        self.choose_image_button = QPushButton("Choose Background Image", self)
        self.choose_image_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.choose_image_button.clicked.connect(self.choose_background_image)
        layout.addWidget(self.choose_image_button)

        # Set the layout
        self.setLayout(layout)

        # Initialize background image and color
        self.background_image = None
        self.background_color = None

    def resizeEvent(self, event):
        """Override the resize event to scale the background image."""
        if self.background_image:
            self.set_background_image(self.background_image)

        # Ensure the layout and text adjust properly with window size
        self.adjustSize()

        super().resizeEvent(event)

    def choose_font(self):
        """Open a font dialog for the user to select a font."""
        font, ok = QFontDialog.getFont()
        if ok:  # If the user selects a font
            self.quote_label.setFont(font)
            self.adjustSize()  # Adjust size to fit the quote

    def choose_background_color(self):
        """Open a color picker for the user to choose a background color."""
        color = QColorDialog.getColor()
        if color.isValid():
            # Set background color for the main window
            self.background_color = color
            self.setStyleSheet(f"background-color: {color.name()};")
            self.update_text_color_based_on_background(color)

    def choose_background_image(self):
        """Allow the user to choose a background image."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.bmp *.jpeg)")
        file_dialog.setViewMode(QFileDialog.List)
        if file_dialog.exec_():
            image_path = file_dialog.selectedFiles()[0]
            # Start a worker thread to load and scale the image
            self.image_worker = BackgroundWorker(image_path, self)
            self.image_worker.image_loaded.connect(self.set_background_image)
            self.image_worker.start()

    def set_background_image(self, pixmap):
        """Set the background image for the window."""
        # Scale the image to fit the window size
        scaled_pixmap = pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        
        brush = QBrush(scaled_pixmap)
        palette = self.palette()
        palette.setBrush(QPalette.Background, brush)
        self.setPalette(palette)

        self.background_image = scaled_pixmap  # Save the image for resizing

        # Update the text color based on the background image brightness
        self.update_text_color_based_on_background(pixmap)

    def update_text_color_based_on_background(self, background):
        """Update text color based on the background brightness (light/dark)."""
        if isinstance(background, QColor):  # if the background is a color
            color = background
        else:  # If background is an image
            color = self.get_dominant_color(background)

        brightness = color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114  # Calculate brightness
        if brightness < 128:  # Dark background
            self.quote_label.setStyleSheet("color: white; font-size: 16px; padding: 20px; text-align: center;")
        else:  # Light background
            self.quote_label.setStyleSheet("color: black; font-size: 16px; padding: 20px; text-align: center;")

    def get_dominant_color(self, pixmap):
        """Extract the dominant color of the image (approximated)."""
        image = pixmap.toImage()
        width = image.width()
        height = image.height()
        pixel_count = width * height
        r, g, b = 0, 0, 0

        for x in range(width):
            for y in range(height):
                color = QColor(image.pixel(x, y))
                r += color.red()
                g += color.green()
                b += color.blue()

        return QColor(r // pixel_count, g // pixel_count, b // pixel_count)

    # Method to get a new quote (online or local)
    def get_quote(self):
        online_quote = fetch_online_quote()
        return online_quote if online_quote else random.choice(local_quotes)

    # Method to update the label with a new quote
    def show_new_quote(self):
        self.quote_label.setText(self.get_quote())
        self.adjustSize()  # Adjust the window size based on the quote length


# Main function to run the app
def main():
    app = QApplication(sys.argv)
    window = QuoteCookieApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
