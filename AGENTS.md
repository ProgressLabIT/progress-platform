# Global interactions
- If you are uncertain about the intention of the request, ask questions to clarify
- Always evaluate the input and think if it may miss important information to carry out the request, then ask follow up questions to fill in the blanks
- Prefer asking questions to get a precise context rather than just trying things out right away
- Whenever a task requires changing more than a few lines of code in a single place, don't make changes unless the user explicitly tells you to do so. Explain your idea first and get feedback.


# Client side code
- Whenever adding new text to webapps always add translations in related language files in the src/i18n folder
- use pinia for state management outside of components, unless there's a vuex store existing already
- never use props for data that is available in vuex or pinia, take it from the store within the component
