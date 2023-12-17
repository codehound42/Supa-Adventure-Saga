# Supa-Adventure-Saga

Supa Adventure Saga is an interactive text-based roleplaying game powered by AI, where you create your character and embark on adventures. Using GPT as your Dungeon Master (DM), the game offers a blend of storytelling and player agency, immersing you in a world of fantasy and intrigue.

Supa Adventure Saga is a small side project for the [Supabase Launch Week X Hackathon (December 2023)](https://supabase.com/blog/supabase-hackathon-lwx). There are many opprotunies for improvement and making the game more advanced, but we hope you enjoy the game as it is.

## Game Overview

In the small village of Eldenwood, you find yourself in the cozy Drunken Dragon Inn. A mysterious figure offers you a quest to investigate the haunted ruins of Graystone Castle, believed to be the source of recent villager disappearances. With a map and promise of gold, you set out to uncover the secrets lurking in the shadowy depths of the castle.

Your quest is to uncover the secrets lurking in the shadowy depths of the castle.

## Supabase

We use supabase for storing the message history of the game. During play relevant parts are retrieved based on the current prompt of the player. The idea is to add long term memory context to the game in addition to the recent most messages.

## Setup
- Clone the repository
- Install dependencies: Install the required Python packages including Streamlit and LangChain.
- Configure Supabase:
    - Set up a Supabase project and postgres database
    - Fill out the Supabase keys in a secrets.toml file in .streamlit (c.f. secrets.toml.example)
- Configure OpenAI API Key: Enter your OpenAI API key in the Streamlit sidebar once the game is running to authenticate.

## Playing the Game

Run the application:
```bash
streamlit run app.py
```

Once the game is running follow the prompts to make your character and begin your adventure.
