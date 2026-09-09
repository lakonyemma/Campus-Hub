# Campus Hub

Android-first academic companion with a contextual AI assistant called Smith.

## First build scope

- Academic dashboard
- Timetable
- Assignment progress
- Study workspace
- PDF selection
- Smith assistant modes
- Notification foundation
- Over-the-air update foundation
- Profile and update control

## PDF AI flow

1. Student selects a PDF in Study.
2. Mobile app uploads it to the Campus Hub API.
3. Backend extracts and chunks text.
4. Chunks are stored under the relevant course.
5. Smith retrieves only the relevant passages for summaries and questions.
6. Generated results can be saved as summaries, flashcards and quizzes.

## Updates

Campus Hub uses `expo-updates`.

- Compatible JavaScript and interface changes can arrive over the air.
- Native dependency or Android permission changes require a new installed binary.
- Android package id stays `com.lakonyemma.campushub`.
- Version codes increase instead of changing the package id, so Android treats new APK/AAB releases as updates.

## Run

```bash
npm install
npx expo start
```

For an installable Android preview:

```bash
npm install -g eas-cli
eas login
eas build --platform android --profile preview
```

## AI backend

Set:

```env
EXPO_PUBLIC_API_URL=https://your-campus-hub-api.example.com
```

The app expects:

`POST /assistant/chat`

The next backend milestone adds PDF ingestion, course memory, timetable context, assignment context and secure user accounts.
