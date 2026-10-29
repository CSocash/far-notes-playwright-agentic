# User Flows

Step-by-step user journeys through FAR Notes, each with expected results. Part of the `far-notes-domain` skill; see `SKILL.md` for vocabulary and selectors and `business-rules.md` for the rules behind each step.

## Example flow #1: Create an account and sign in
1. Go to `/login` and click **Create an account**, which opens `/create-account`.
2. Fill in **Username**, **Email address** and **Password** (at least 15 characters), then click **Create account**.
3. Expected: the form hides and "Account created successfully. Return to the login page to sign in." appears. The user is **not** signed in yet.
4. Go back to `/login`. Enter the username *or* the email in **Username or email**, enter the password and click **Sign in**.
5. Expected: the page redirects to `/`. The header shows the username, the part shows **PART 91**, and the status reads "Connected to SQLite". The starter Part 91 sections are listed with 0% progress.
- Failures: a duplicate username or email shows "Account creation was not successful. That username or email is already in use." Bad credentials show "Username or password is incorrect."

## Example flow #2: Study a subsection
1. While signed in on `/`, find a study item such as `91.103(a)`.
2. Check **Mark 91.103(a) as covered**.
3. Expected: the label changes to "Yes", the date fills in with today's local date, and Covered, To go and the progress % update right away.
4. Type a note in **Notes for 91.103(a)** and click elsewhere so the field loses focus.
5. Reload the page. Expected: covered, the date and the note are all still there.
6. Uncheck the item. Expected: the label returns to "No" and the date clears.

## Example flow #3: Switch between Part 91 and Part 61
1. On `/`, choose **Part 61** in the part dropdown.
2. Expected: the brand shows **PART 61**, the page title becomes "Part 61 Study Log", the search box clears, the filter resets to **All**, and the Part 61 starter sections load.
3. Progress on each part is tracked separately. Covering an item in Part 61 doesn't change the Part 91 counts.

## Example flow #4: Search and filter
1. Type into **Search regulations or notes...** (or press `/` to focus the box). Matching is on heading, reference such as `91.103(b)`, subsection title and notes.
2. Expected: only matching items and their section headers stay visible, and the footer reads "Showing X of Y study items".
3. Click **To study** or **Covered** to narrow further. Each button shows its count.
4. Search for text that matches nothing. Expected: the table hides and "No study items found" appears.
5. Press **Escape** in the search box. Expected: the search clears and the full list returns.

## Example flow #5: Add a custom section and edit its heading
1. Click **+ Add section**.
2. Expected: the toast reads "New section added. Enter a regulation number to get started.", a new section with one "Entire section" item appears at the bottom, and its heading input has focus.
3. Type a heading such as `91.999 — My custom topic` and press **Enter**.
4. Expected: the heading saves and becomes an eCFR link. The section has an **Edit** button, while starter sections don't.
5. Click **Edit**, change the text and press **Escape**. Expected: the heading reverts to what it was when editing started, and that original text is saved again (overwriting any keystrokes that already autosaved). Reload to confirm.

## Example flow #6: Forgot and reset password
1. On `/login`, click **Forgot password?**, enter the email and click **Request reset link**.
2. Expected: "If an account matches that address, a reset link is available in the local server terminal." appears, whether or not the account exists.
3. Copy the `http://127.0.0.1:3000/reset-password#token=…` link from the server console and open it.
4. Enter a matching **New password** and **Confirm new password** (at least 15 characters) and click **Set new password**.
5. Expected: "Password updated. You can now sign in with your new password." appears. Existing sessions for that user are signed out, the old password no longer works and the new one does.
- Failures: mismatched passwords show "The passwords do not match." An expired or reused link shows "This reset link is invalid or has expired. Request a new one."

## Example flow #7: Log out and access control
1. On `/`, click **Log out**. Expected: the page redirects to `/login`.
2. Visit `/` again. Expected: it redirects to `/login`, and calling `/api/regulations` directly returns 401.
3. Sign in, then visit `/login` or `/create-account`. Expected: both redirect to `/`.
4. With two accounts, items covered by one user never show up for the other.
