# D-JAI

Framework for an autonomous DJ with live interactions and AI-generated music. Created for a Brainjuice event.

## Table of Contents

- [Project Description](#project-description)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Project Description

D-JAI is a framework designed to create an autonomous DJ capable of live interactions and generating music using AI. The goal is to seamlessly blend AI-generated music with live DJ interactions to create unique and dynamic performances.

## Installation

To get started with D-JAI, follow these steps:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/0xbadc0ffe/D-JAI.git
    cd D-JAI
    ```

2. **Install the necessary dependencies:**

    ```bash
    # If using pip
    pip install -r requirements.txt
    ```

## Usage

### Setup your APIs

- SUNO API -> [suno-api github](https://github.com/gcui-art/suno-api)
- OPENAI API -> [openai quickstart](https://platform.openai.com/docs/quickstart)

Add them in  ``` src/.env ```.

### Add your songs
It is advised to add some songs in the ```queue``` folder before the live-generation so that the ```src/streamer.py``` has something to play in the meantime.
Just donwload a bunch and add them to the folder :)

### Run it!

You can start the song-streaming process with 

``` bash
python src/streamer.py
```

that will automatially play the songs contained in ``` queue ```.
While, in parallel, the song-generating process can be started with

``` bash
python src/app.py
```

that will open a local interface to generate more songs that will be added to ``` queue ```.
To interact with it, visit yout localhost at [127.0.0.1:5000](http://127.0.0.1:5000)



### Creating a Song

Within the interface you will find 5 fields: *Idea, Genres/Musical Characteristics, Title, Lyrics, Language*.
Specify what you want and let GPT autofill the missing ones! It is recommended to specify at least one field (preferably Idea) to avoid generating songs about boring topics.
Mind that the song generation is biased, as described below.

### Generation Biases

The song generation is biased thorugh the prompt we provide to GPT. To regulate **language** and **musical genres** biases you can modify the  ``` src/biases.json ``` file, while for more sophisticated biases you can directly alter the prompt format within ```src > app.py > generate_song_info```.


### Song Queue

By deafult the new songs added to ``` queue ``` while the song-streaming process is running have max priority, therefore they will be next in the playing queue.
Removing songs from the same folder during runtime will also remove them from playing queue. You can verify the current playing queue in the log folder.



## Contributing

We welcome contributions to enhance the D-JAI project. To contribute, please follow these guidelines:

1. **Fork the repository:**

    Click the "Fork" button at the top right of this repository's GitHub page to create a copy of the repository under your own GitHub account.

2. **Clone your forked repository:**

    ```bash
    git clone https://github.com/your-username/D-JAI.git
    cd D-JAI
    ```

3. **Create a new branch:**

    ```bash
    git checkout -b feature/your-feature-name
    ```

4. **Make your changes:**

    Implement your feature or fix a bug. Ensure your code adheres to the project's coding standards.

5. **Commit your changes:**

    ```bash
    git add .
    git commit -m "Description of the feature or fix"
    ```

6. **Push your changes to your forked repository:**

    ```bash
    git push origin feature/your-feature-name
    ```

7. **Create a pull request:**

    Go to the original repository and create a pull request from your forked repository. Provide a clear description of your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For any questions or inquiries, please dont contact us

---

*Note: This project was created for a Brainjuice event.*





