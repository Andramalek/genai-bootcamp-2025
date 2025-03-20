BACKEND IMPLEMENTATION
Hypothesis and Technical Uncertainty
When I started this project, I was really nervous because:
I had never used Go before (only knew Python a little bit)
I didn't know how to make a proper web server
Databases seemed A bit daunting (especially SQL stuff)
I wasn't sure how to organize a "real" project with multiple folders
My main hypothesis was that I could build a backend server that would store and manage vocabulary words, but I was worried it might be too complex for my skill level.
Technical Exploration
During my learning journey, I tried these things:
Project Structure:
Learned about Go project organization (cmd, internal, db folders)
Found out about something called "mage" for automating tasks
Had to understand what "go.mod" and "go.sum" files do
Discovered that "internal" means private code (that was new!)
Database:
Used SQLite because it seemed simpler than big databases
Made a words.db file to store vocabulary
Learned about migrations (though I'm still not sure what they do)
Found out about seeding data (putting starter data in the database)
Web Server:
Used something called "Gin" framework (it had good tutorials)
Had to learn about:
Handlers (they handle web requests)
Models (they represent data)
Services (they do the business logic)
Added CORS support (still don't fully understand it but it makes the frontend work)
Build Tools:
Made a magefile.go that helps set up the project
It can:
Create the database
Run migrations
Add seed data
Though some parts are still TODO (I didn't finish everything)
Final Observations and Outcomes
What Worked Well:
The server actually runs! (I was surprised)
Database gets created automatically
Project structure looks professional
Code is organized in different packages
What I Learned:
Go is different from Python (no indentation!)
Project organization is really important
Dependencies need to be managed carefully
Automation helps a lot (thanks to magefile)
Problems I Still Have:
Some TODOs in the magefile
Not sure if my error handling is good
Migrations aren't implemented yet
Need more tests probably
Things I Want to Add:
Finish the migrations
Add more database features
Make better error messages
Add user authentication maybe

FRONTEND IMPLEMENTATION
Hypothesis and Technical Uncertainty
I had never used TypeScript before (JavaScript was hard enough!)
There were so many UI components to build
I didn't know how to make a "single page application"
React seemed complicated with all its hooks 
I was unsure if I could make the app look professional
My main hypothesis was that I could create a user-friendly interface for learning Japanese, but I wasn't sure if I could handle all the modern web development tools and make it look good.
Technical Exploration
Here's what I tried and learned:
Modern Tools Setup:
Used Vite instead of Create React App (faster)
Learned a little bit of TypeScript but need to learn much more
Used something called "shadcn/ui" for nice-looking components
Learned about package.json and dependencies
Component Organization:
Made different pages for:
Dashboard (main page)
Study Activities
Words
Groups
Sessions
Settings
Used React Router for navigation (it's like magic!)
Made a layout component that wraps everything
UI Components:
Used lots of Radix UI components like:
Accordion (for expandable sections)
Dialog (for popups)
Navigation Menu
Toast (for notifications)
Learned about themes and dark mode
Had to style everything with CSS (so many classes!)
TypeScript Learning:
Had to add types to everything
Learned about interfaces and types
Got lots of red squiggly lines in VS Code
Finally understood why types are useful
Final Observations and Outcomes
What Worked Well:
The app actually looks professional!
Navigation between pages works smoothly
Components are reusable
Dark mode works (that was a bonus!)
What I Learned:
TypeScript is actually helpful (even though it's annoying sometimes)
Component libraries save a lot of time
React Router makes navigation easier
Organization is super important in big projects
Problems I Still Have:
Some TypeScript errors I don't understand
Components could be more reusable
Need to add more error handling
Loading states could be better
Things I Want to Add:
More animations
Better mobile support
Offline mode maybe
More accessibility features

VOCAB IMPORTER
Hypothesis and Technical Uncertainty
When I started this project, I had several questions and uncertainties:
I wasn't sure if I could make an AI generate proper Japanese vocabulary with correct kanji characters
I was worried about handling Japanese text in a web application
I didn't know if I could properly break down kanji words into their component parts
I was uncertain about using modern web frameworks like Next.js and TypeScript
My main hypothesis was that I could create a tool that would help language learners by automatically generating themed vocabulary lists with proper kanji breakdowns, but I wasn't sure if the AI would be reliable enough.
Technical Exploration
During my exploration phase, I tried several approaches:
Framework Choice:
I decided to use Next.js because it seemed easier than building everything from scratch
I struggled with TypeScript at first (got errors about missing types for 'process' and 'next/server')
Had to learn about installing type definitions (@types/node) which was new to me
AI Integration:
Found out about the Groq API which could help generate Japanese vocabulary
Learned how to handle API keys safely using environment variables
Had to write a lot of error handling because the AI sometimes gave weird responses
Component Building:
Made a VocabularyImporter component that handles:
User input for themes
API calls to generate vocabulary
Displaying results
Error handling
Used some UI components I found (like buttons and cards)
Added a copy-to-clipboard feature which was cool
Japanese Text Handling:
Had to learn about kanji character detection using Unicode ranges
Made functions to check if text contains actual Japanese characters
Added validation to make sure the AI didn't give English placeholders
Final Observations and Outcomes
What Worked Well:
The app successfully generates Japanese vocabulary based on themes
It breaks down kanji into components with readings
Has error handling when things go wrong
Includes a nice user interface with loading states and notifications
What I Learned:
Modern web development is more complex than I thought
Working with APIs requires lots of error checking
TypeScript is hard at first but helps catch mistakes
Japanese text processing needs special consideration
Problems I Still Have:
Sometimes the AI generates weird or incorrect vocabulary
The app might be slow when the API is busy
Some kanji breakdowns might not be 100% accurate
Future Improvements:
Add a dictionary lookup to verify the vocabulary
Save favorite vocabulary lists
Add pronunciation audio
Make it work offline somehow

OPEA Implementation
Hypothesis and Technical Uncertainty
I had never used Docker before (containers a mystery to me and
even now I still feel I'm scratching the surface)
I didn't know how LLM's work with containers
I was confused about networking and ports
API calls seemed complicated
I wasn't sure how to handle environment variables
My main questions were:
Could I get an AI model running on my computer?
Would I be able to communicate with it through an API?
How do I make sure it's secure and works with other services?
Technical Exploration
Here's what I learned and tried:
Docker:
Learned about docker-compose (it's like a recipe for containers!)
Found out about:
Container networks (bridge mode)
Port mapping (9000:11434)
Environment variables
Used the ollama/ollama image (it's like a pre-made container)
Network Configuration:
Had to figure out how to get my IP address (used ifconfig) this was frustrating.
Learned about ports and why they matter
Found out about proxies and no_proxy settings
Had to understand host vs container networking
LLM Integration:
Used the Ollama API
Learned how to:
Pull models (like llama3.2:1b)
Make generate requests
Handle API responses
Found out models are really big! (I think my system can only handle the small 1b model of llama3.2 at best)
Environment Setup:
Had to set variables like:
LLM_MODEL_ID
HOST_IP
Proxy settings
Learned about environment files
Final Observations and Outcomes
What Worked Well:
Got Ollama running in Docker!
Could make API calls to generate text
Understood container networking better
Learned about model management
What I Learned:
Docker makes deployment easier
APIs need proper configuration
Environment variables are important
Models take up lots of space
Problems I Still Have:
Models disappear when container stops
Need to handle storage better
Not sure about security best practices
API error handling needs work
Cool Discoveries:
You can run AI models locally!
Docker makes sharing services easier
Bridge networks are actually useful
curl is a handy tool for testing
Things I Want to Add:
Persistent storage for models
Better error handling
Security improvements
Model performance monitoring
