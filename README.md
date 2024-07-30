# AI Arena Project

## Project Goals and Objectives
The goal of the AI Arena project is to create an online game where players can create unique characters, describe them textually, and use a neural network to visualize these characters, participate in battles, and compete with other players. The project leverages the capabilities of Google's multimodal model, Google Gemini, to generate images, descriptions, and battle analyses.

### Project Objectives:
- Provide a platform for creating and managing characters.
- Develop dynamic combat mechanics using neural networks.
- Implement automatic, semi-automatic, and manual game modes.
- Ensure a user-friendly interface for players, administrators, and spectators.
- Implement a communication and chat moderation system with automatic message translation.
- Utilize Google Gemini's multimodal model for generating character images and descriptions, analyzing battles, and creating video content.

## Interface

### Player Interface:
- **Main Player Page**:
  - Text field for character name: Players enter their character's name (multiple characters can be created, edited, and set against specific opponents in the future).
  - Text field for character attributes: Players enter character attributes (weapons, strength, armor, etc.).
  - Voice input: Ability to dictate character attributes using Google Speech-to-Text.
  - Example prompts: Minimal prompts for structuring character descriptions.
  - Example of character attribute description.

- **Game Mode Selection**:
  - Automatic Mode: The neural network fully controls all actions.
  - Semi-Automatic Mode: Players can input commands via text or voice, and the neural network adjusts battle tactics based on these commands.
  - Manual Mode: Players describe all actions of their character themselves.

- **Chat**:
  - Message sending: Ability to send messages to the general chat.
  - Automatic translation: Messages are translated into the player's language using Google Gemini if this mode is enabled.
  - Moderation: Messages are automatically moderated to remove offensive content.

- **Battle Display**:
  - Text descriptions of attacks and defenses: The neural network describes each attack and defense.
  - Key moment generation: Every six moves/combinations/tricks, an image of the key moment is generated. The window shifts as the battle progresses. The size of the window is set by a parameter in the settings.

### Administrator Interface:
- **Chat Management**:
  - Message moderation: Ability to moderate and delete messages.

- **Neural Network Settings**:
  - Parameter adjustment: Adjusting temperature, top-p, top-k, and other neural network parameters.
  - Action and defense assessment settings: Setting specific actions, types of attacks, and defenses.
  - Battle assessment: Setting metrics or criteria for evaluating battles.

- **User Management**:
  - Viewing and managing users: Ability to view and manage user profiles (warn, block, etc.).

### Spectator Interface:
- **Character Display**:
  - Character information: Displaying the name, attributes, and image of characters.
  - Battle description in general chat (commentator mode): Text description of each battle with key moments and images.

## Game Mechanics

### Character Creation:
- Players enter the name and attributes of their character.
- The neural network generates an image and attributes of the character based on the description.

### Battle Mechanics:
- **Initial Point Assignment**:
  - Each character is assigned a certain number of health points based on their attributes.

- **Point Calculation During Battle**:
  - The neural network generates attacks and defenses with certain effectiveness and strength.
  - Each effective hit deducts a certain number of points from the opponent.

- **Determining the Winner**:
  - The battle continues until one character runs out of health points.
  - The character whose health points reach zero first loses, and their opponent is declared the winner.

- **Bonuses for Successful and Interesting Moves**:
  - The neural network awards bonus points for particularly successful and interesting moves.

### Game Modes:
- **Automatic Mode**:
  - The neural network fully controls all actions and decisions of the character during the battle.

- **Semi-Automatic Mode**:
  - Players can input commands via text or voice.
  - Commands can include any actions available to the character, taking their attributes into account.
  - The neural network combines player suggestions with its strategy to create optimal attacks and defenses.

- **Manual Mode**:
  - Players fully describe all actions of their character.

## Use of Google Gemini Model in AI Arena Project
- **Image and Description Generation**:
  - Google Gemini is used to create character images based on players' textual descriptions and attributes.

- **Battle Analysis**:
  - The neural network analyzes battles, generates text descriptions of attacks and defenses, assigns points, and determines the winner.

- **Post-Battle Video Creation**:
  - Google Gemini generates scripts and texts for videos based on character images, descriptions, and battle descriptions.
  - Visual elements are created and the video is automatically edited.
  - The generated video is published on the platform for viewing by participants and spectators.

- **Chat Message Translation and Moderation**:
  - All messages are automatically translated into English and stored in a database.
  - Based on players' local language settings, messages are translated into their native language and displayed in their chat window if this parameter is set.
  - Messages are automatically moderated to remove offensive content.

## Technical Requirements

### Web Page:
- The game will be browser-based, opening seamlessly on both mobile and desktop devices.
- The main page will be a single-page application (SPA) with the necessary information.
- Separate single-page views for each player and separate views for spectators.

### Authentication and Database:
- Using unique IDs based on cookies for player authentication.
- Using SQLite to store player information and attributes.
- Creating a separate table to save chat messages and maintain them for a long time.

## Conclusion
The AI Arena project provides a unique platform for creating and managing characters, participating in battles, and interacting with other players. Utilizing the capabilities of the Google Gemini model ensures high-quality generation of images and descriptions, battle analysis, and video creation. The flexibility of game modes and well-thought-out interface system make the game accessible and engaging for all participants.

______________________________________________________________________
* Top-p (also known as "nucleus sampling")
Imagine we have a box with balls of different colors, each representing a possible model response. Top-p helps select only the most likely options from this box.
How it works:
1. The model calculates the probability of each possible response.
2. Then it selects only those options that sum up to probability p (e.g., 0.9 or 90%).
3. From the remaining options, the model randomly selects one for the response.
Thus, top-p allows considering only the most likely responses while maintaining an element of randomness, making the responses more diverse.

* Top-k
Now imagine we have a box with balls, but instead of probabilities, each ball has its rank written on it (e.g., first place, second place, and so on).
How it works:
1. The model selects the k most likely options (e.g., k = 10).
2. From these k options, the model randomly selects one for the response.
Top-k limits the model's choice to a fixed number of the most likely options, making the responses more predictable yet still diverse.



======================================
del logging from requirements
del dotenv from requirements