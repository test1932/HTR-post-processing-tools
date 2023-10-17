import pygame
import sys
import json

# TODO adding selection
# constants
HEIGHT = 800
WIDTH = 1200

class textBox(pygame.Rect):
    """class for creating textbox based on text prediction area.
    """
    MAX_CHARS = 20
    
    def __init__(self, left, top, width, height, pred, font):
        """init method.

        Args:
            left (int): x position of textbox.
            top (int): y position of textbox.
            width (int): width of textbox.
            height (int): height of textbox.
            pred (dict): dict of prediction the textbox represents.
            font (pygame.Font): font of text, needs to be monospace.
        """
        super().__init__(left, top, width, height)
        self.cursorPos = len(pred['DetectedText'])
        self.pred = pred
        self.font = font
        
    def setText(self, newPred):
        """sets the prediction dict the textbox represents.

        Args:
            newPred (dict): prediction dict the textbox represents.
        """
        self.pred = newPred
        self.cursorPos = len(newPred['DetectedText'])
        
    def incrementCursor(self, increment):
        """increments the position of the cursor in the textbox by increment.

        Args:
            increment (int): value to increment position of cursor by (wraps 
            around).
        """
        self.cursorPos = (self.cursorPos + increment) \
            % (len(self.pred['DetectedText']) + 1)
    
    def deleteChar(self):
        """removes the character immediately before the cursor.
        """
        if self.cursorPos > 0:
            self.pred['DetectedText'] = \
                self.pred['DetectedText'][:self.cursorPos - 1] + \
                self.pred['DetectedText'][self.cursorPos:]
            self.cursorPos -= 1
    
    def getText(self):
        """returns the text in the textbox.

        Returns:
            str: text in the text box.
        """
        return self.pred['DetectedText']
    
    def addChar(self, char):
        """adds a char to the position immediately after the cursor and
        increments cursor position.

        Args:
            char (str): unicode string representing a character or an empty
            string.
        """
        text = self.pred['DetectedText']
        self.pred['DetectedText'] \
            = f'{text[:self.cursorPos]}{char}{text[self.cursorPos:]}'
        self.cursorPos += len(char)
    
    def getTextToDisplay(self):
        """produces the string to display on the textbox on screen

        Returns:
            str: text to display.
        """
        beforeChars = self.pred['DetectedText'][:self.cursorPos]
        if (l:=len(beforeChars)) >= textBox.MAX_CHARS:
            return(self.cursorPos - 20, self.cursorPos, \
                   beforeChars[l - textBox.MAX_CHARS:])
        return (0, min(20, len(self.pred['DetectedText'])), \
                self.pred['DetectedText'][:20])
    
    def display(self, surface):
        """blit the textbox onto the surface provided.

        Args:
            surface (pygame.Surface): surface to display the textbox on.
        """
        pygame.draw.rect(surface, (200, 200, 255), self)
        pygame.draw.rect(surface, (0, 0, 0), self, 2)
        startIndex, endIndex, textToDisplay = self.getTextToDisplay()
        text = self.font.render(textToDisplay, False, (0,0,0))
        surface.blit(text, (self.x + 5, self.y + 5))
        
        charWidth = text.get_width()/len(textToDisplay) \
            if len(textToDisplay) else 0
        xCursor = charWidth * (self.cursorPos - startIndex) + 5
        pygame.draw.line(surface, (255, 50, 50), \
            (xCursor + self.x, self.y + 5), \
            (xCursor + self.x, self.y + self.height - 5), 1)


def makeImage(imageFname):
    """acquires and resizes the specified image.

    Args:
        imageFname (str): path to image to display.

    Returns:
        pygame.Surface: image to display on the screen.
    """
    image = pygame.image.load(imageFname)
    maxWidth = int(0.6 * WIDTH)
    maxHeight = int(0.7 * HEIGHT)
    factorOfWidth = image.get_width() / maxWidth
    factorOfHeight = image.get_height() / maxHeight
    dominatingFactor = 1 / max(factorOfWidth, factorOfHeight)
    image = pygame.transform.scale(image, 
                                   (dominatingFactor * image.get_width(),\
                                    dominatingFactor * image.get_height()))
    return image

def renderPredictions(surface, predictions, x, y, width, height, font, high):
    """displays the predicted text bounding boxes on the image.

    Args:
        surface (pygame.Surface): surface to display predictions on.
        predictions (list): list of dicts representing text predictions and
        bounding boxes.
        x (int): x position of image on surface.
        y (int): y position of image on surface.
        width (int): width of image.
        height (int): height of image.
        font (pygame.Font): ignore, can be None.
        high (int): index of highlighted prediction in the list.
    """
    i = 0
    for pred in predictions:
        # if ' ' in pred['DetectedText']:
        #     continue
        
        dims = pred['Geometry']['BoundingBox']
        boundingBox = pygame.Rect(x + dims['Left'] * width,\
                                  y + dims['Top'] * height,\
                                  dims['Width'] * width,\
                                  dims['Height'] * height)
        col = (255, 0, 0) if i != high else (0, 255, 0)
        pygame.draw.rect(surface, col, boundingBox, 1 + (i == high))
        i += 1

def renderTextEditor(surface, predictions, high, font, textBoxEdit):
    """display column of text of predictions.

    Args:
        surface (pygame.Surface): surface to display predictions on.
        predictions (list): list of text prediction dicts.
        high (int): index of highlighted prediction.
        font (pygame.Font): font to display text predictions in.
        textBoxEdit (textBox): textBox object where user can edit.
    """
    background = \
        pygame.Rect(0.75 * WIDTH, 0.05 * HEIGHT, 0.2 * WIDTH, 0.9 * HEIGHT)
    pygame.draw.rect(surface, (200,200,200), background)
    pygame.draw.rect(surface, (50,50,50), background, 2)
    textBoxEdit.display(surface)
    for i, pred in enumerate(predictions[high + 1:][:20]):
        text = font.render(pred['DetectedText'][:20], False, (0,0,0))
        surface.blit(text, (0.75 * WIDTH + 10, 0.05 * HEIGHT + 50 + i * 30))

def runPygameUI(imageFname, predictions):
    """main pygame loop.

    Args:
        imageFname (str): path to image.
        predictions (str): path to Rekognition JSON.
    """
    pygame.init()
    pygame.display.set_caption("editor")
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    titleFont = pygame.font.SysFont('gabriola', 60)
    notationFont = pygame.font.SysFont('arial', 20)
    basicTextFont = pygame.font.SysFont('courier new', 15)
    textBoxEdit = \
        textBox(0.75 * WIDTH + 10, 0.05 * HEIGHT + 10, 0.2 * WIDTH - 20, 30,\
        predictions[0], basicTextFont)
    
    running = True
    image = makeImage(imageFname)
    title = titleFont.render("Post Processing Editor", False, (0,0,0))
    highlight_hist = 0
    highlight = 0
    
    while running:
        window.fill('#216367')
        window.blit(image, ((x:= (0.05 * WIDTH)), (y := (0.2 * HEIGHT))))
        window.blit(title, (0.05 * WIDTH, 0.05 * HEIGHT))
        renderPredictions(window, predictions, x, y, image.get_width(),\
            image.get_height(), notationFont, highlight)
        
        if highlight != highlight_hist:
            textBoxEdit.setText(predictions[highlight])
        highlight_hist = highlight
        renderTextEditor(window, predictions, highlight, basicTextFont, \
            textBoxEdit)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    highlight = (highlight + 1) % len(predictions)
                elif event.key == pygame.K_UP:
                    highlight = (highlight - 1) % len(predictions)
                elif event.key == pygame.K_LEFT:
                    textBoxEdit.incrementCursor(-1)
                elif event.key == pygame.K_RIGHT:
                    textBoxEdit.incrementCursor(1)
                elif event.key == pygame.K_BACKSPACE:
                    textBoxEdit.deleteChar()
                elif event.key == pygame.K_DELETE:
                    if not len(predictions) > 1:
                        continue
                    del predictions[highlight]
                    highlight = max(0, highlight - 1)
                    textBoxEdit.setText(predictions[highlight])
                else:
                    textBoxEdit.addChar(event.unicode)
                
        pygame.display.update()

def readData(fname):
    """reads Rekognition formatted JSON into dict

    Args:
        fname (str): path to Rekognition JSON file

    Returns:
        tuple: tuple of metadata dict and predictions dict.
    """
    file = open(fname, 'r')
    data = file.read()
    file.close()
    jsonData = json.loads(data)
    keys = list(jsonData.keys())
    return (jsonData[keys[0]], jsonData[keys[1]])

def main(imageFname, jsonFname):
    """main method.

    Args:
        imageFname (str): path to image.
        jsonFname (str): path to Rekognition data.
    """
    metadata, predictions = readData(jsonFname)
    runPygameUI(imageFname, predictions)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        exit()
    main(sys.argv[1], sys.argv[2])