# Smart Flash Cards
#### Video Demo:  <https://youtu.be/wE-U1O93I5I>
#### Description:
This is my final Project for HarvardX: CS50's Introduction to Computer Science. It's a web application made using HTML, CSS, JavaScript, Flask and SQL based on concept of spaced repetition, which involves reviewing information at increasing intervals of time. The user is only required to enter the information in the form of questions and answers, called flash cards and the website automatically decides when it need to be revised.

##### How it works?
###### Type
Each flash card requires the user to either type out the answer, for information like dates, name etc; or to tell the system whether they knew the answer or not, for more conceptual information. This is the `type` of the flash card, and is chosen by the user, it can be either `enter` for the former or `self` for the latter.

###### Tags
Each flash card can be allotted a tag, which is created by the user, by default each flash card is `Untagged`.

###### Level
Each flash card has a level, from 1 to 5, this determines how often a flash cards need to be revised; every day for level-1, every 2 days for level-2, every 7 days for level-3, every 14 days for level-4 and every 30 days for level-5.

Each flash card is at level-1 when created.

###### Streak
Each card also has a streak associated with it, if the user gets the cards correct, it's increased by 1; if the user gets it wrong, the streak is reset to 0 and the flash card's level is reduced by 1. If a flash card's streak becomes equal to its level, the level is increased by 1 and the streak is reset to zero.

Each flash card has a streak of 0 when created.

Thus, a level-4 cards is revised every 14 days and needs to be answered correctly 4 consecutive times to move to level-5. If it's answered incorrectly once, it's moved back to level-3 with a streak of 0.

###### Archive
Each flash card can be archived, this causes it to not to revised until it's unarchived. When that happens, it's treated as a newly created flash cards, and thus is of level-1, with a steak of 0.

###### Rescheduling

If the user doesn't revise any number of flash cards, they are automatically rescheduled over the next 7 days, their level is reduced by 1 or 2 and their streak is reset to 0 when the user logs into the website. This ensures that any skipped flash cards are revised while minimising extra load.

##### Technologies Used
- HTML
- CSS
- JavaScript
- Bootstrap
- Python
- Flask Library
- SQLite
- cs50 Library, for SQL Backend

##### Tables in Database
**File**: `database.db`

###### `users` - username, password
- Keeps track of username and hashed password of each user

###### `tags` - username, name
- Keeps track of the name of each tag that a user has created

###### `cards` - username, question, answer, level, nextDate, tag, type, streak, archived
- Keeps track of each flash card.
- `nextDate` is the next date when the flash card has to be revised.
- `type` can be `self`, if the user wants to inform the system if they knew that answer, or `enter` if they want the type out and submit the answer.
- archived can be `yes` or `no`. It's no by default.

##### Routes and Files:

###### `/register` - Register new accounts
**File:** `register.html`
- It checks if the input is valid, if so, it hashes their password, using the `werkzeug.security` library, and adds it into the `users` table .
- It then sets the username in session to the username of the user

###### `/login` - Logging into existing accounts
**File:** `login.html`
- Cross checks input with the `users` table.
- If so set username in session equal to the username of the user and redirects user to `/`

###### `/` - Homepage
**File:** `index.html`
- This the main page of the website which gives a basic overview of the features of the website along with an option to start revising all the flash cards due today.
- It reschedules any past flash cards that weren't revised on time and reduces their `level` by 1 or 2 and resets their `streak` to 0.
- It redirects the user to the register page if there is no `username` field in `session`.
- If user isn't logged in and opens any route, other than login or register, they are redirected here.

###### `/logout` - Logout from the website
- clears the session
- Redirects user to `/register`

###### `/tags` - View, add, edit and delete tags
**File:** `tags.html`
- Shows a list of all tags with the number of flash cards associated with them along with option to edit or delete them.
- Also allows user to add new tags to the `tags` table.

###### `/editTag` - Edit an existing tag
**File:** `editTag.html`
- Edits the tag's name in the `tags` table
- Edits the name of the `tag` in all flash cards where it has been used.

###### `/deleteTag` - Deleting a tag
- Edits the `tag` of any flash cards which had this tag to `Untagged`.

###### `/cards` - View, add, edit, delete, achieve Flash cards
**File:** `cards.html`
- Allows user to add a new flash card by entering it question, answer, tag and type.
- If the input is valid, it adds to data to the `cards` table.
- Shows list of all non-archived flash cards with thier level, tag and next date to revise.

###### `/editCard` - Editing a flash card
**File:** `editCard.html`
- Allows user to edit card without altering it streak, level or next date.
- Each flash card is identified by its question so the original question is passed as an argument in the URL.

###### `/deleteCard` - Deleting a flash card
- Deletes the flash card whose question is an argument in the URL.

###### `/archiveCard` - Archives a card
- The flash card whose question is passed as an argument in the URL, has it `archived` field in the `cards` table set to `yes`

###### `/archivedCards` - View, unarchive and delete archived flash cards
**File:** `archivedCards.html`
- Shows list of all archived cards along with an option to delete and unarchive them.

###### `/unarchiveCard` - Unarchive a flash card
- Edits the `archived` field in `cards` table to `no`

###### `/revise` - Revising a flash card
**File:** `reviseCard_self.html`, `reviseCard_enter.html`
- If this route is called without value of `question` in URL, it randomly selects one of the cards due today and redirect to itself with that question in URL.
- If no card is left for today, it redirects user to `/`.
- If the URL contains a question, the app renders either `reviseCard_self.html` or `reviseCard_enter.html` depending on the flash card's type.
- Within `reviseCard_self.html`, the user has to press the `Show Answer` button to get redirected to `/showAns_show` with the question passed into the URL.
- Within `reviseCard_enter.html`, the user has to type the answer into the input and then press the `Submit` button to get redirected to `/showAns_enter` with the question passed into the URL.

###### `/showAns_show` - Displays answer of flash card
**File:** `/showAns_show.html`
- When method is `GET` it displays the answer of the question in the URL.
- The user has to choose if they got the answer correct or not.
- It then redirects the user to the same route in `POST` method.
- If its method is `POST`, it checks if the answer was correct or not and updates the `cards` table accordingly.
- Then it redirects user to `/revise` i.e. to next card or `/`, if no cards are left for today.

###### `/showAns_enter` - Displays answer of flash card
**File:** `/showAns_enter.html`
- It displays the answer of the question in the URL and if the user got it correct.
- Pressing the `Next` button redirects user to `/revise` i.e. next card or `/`, if no cards are left for today.
