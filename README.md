# Mastodon ALT Text

Updates the alt text of images in Mastodon posts using some local AI.

Note: This is a lounch-time project and could fail in many ways. Use at your own risk.

## Requirements

* A mastodon account of course
* python3
* [ollama](https://ollama.com) installed

## Installation

Create a new mastodon application here: `https://[your instance]/settings/applications`

You will need the following scopes:

* `read:statuses`: needed to get your published posts.
* `profile`: needed to get your profile.
* `write:media`: needed to upload new media with alt text.
* `write:statuses`: needed to update the status.

Pull the required models:

```bash
ollama pull llava:7b # This is the model used to generate the alt text
ollama pull mistral-nemo # This is the model used to translate the alt text
```

Install the requirements and configure the service:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp envrc.example .envrc
## compile the envrc file
sudo systemctl edit --full --force mastodon_alt_text.service
## Copy the contents of mastodon_alt_text.service into the editor
sudo systemctl enable --now mastodon_alt_text.service
```

Now you should be able to read the logs with `journalctl -fu mastodon_alt_text.service`

## Usage

Check if the service has already updated the alt text of your images.

Now you can post on mastodon as usual and the service will update the alt text of the images in your posts.
