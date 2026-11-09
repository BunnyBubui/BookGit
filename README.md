# PM2.5 Forecasting Experiments

Data preparation and CNN/recurrent-model experiments for PM2.5 forecasting. Accuracy and deployment claims require a reproducible evaluation.

## Technology

Python, TensorFlow, pandas, scikit-learn, Firebase Admin.

## Portfolio status

Classification: **supporting**. This description reflects the checked-in implementation. It does not assert production usage, ownership of every team contribution, measured performance or a passing test run.

For a resume, describe only your own contributions and include a screenshot or a reproducible demo. No customer, student, payment or credential data is required to review this code.

## Local configuration

Copy any `*.env.example` files to the corresponding local environment paths and fill in your own values. Never commit these filled files. A removed credential must also be revoked at its provider; deleting a file does not remove it from Git history.

## Review and attribution

Team work and third-party assets retain their original authorship and licensing. Check the implementation and existing package scripts for available commands. Scaffolds and deployment-only copies are not complete application showcases.

## Portable configuration

Set process environment variables before launching the Python scripts. `GOOGLE_APPLICATION_CREDENTIALS` must point to a key stored outside the repository, or use Google Application Default Credentials. Set `FIREBASE_DATABASE_URL` only when using Firebase mode. `BOOKGIT_DATA_DIR` and `BOOKGIT_OUTPUT_DIR` are optional directory overrides; omit them to use project-relative defaults. The example file is a reference, not an automatically loaded secret store. The previously exposed key has been revoked by the account owner.
