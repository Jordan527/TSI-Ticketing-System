<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Jordan527/TSI-Ticketing-System">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">TSI Ticketing System</h3>

  <p align="center">
    A serverless AWS ticketing system for Microsoft Teams 
    <br />
    <a href="https://github.com/Jordan527/TSI-Ticketing-System"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Jordan527/TSI-Ticketing-System/issues">Report Bug</a>
    ·
    <a href="https://github.com/Jordan527/TSI-Ticketing-System/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#key-features">Key Features</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

The TSI Ticketing System is a comprehensive bug ticketing system designed to streamline the process of reporting, tracking, and resolving software issues. Leveraging Python Flask for the backend, Microsoft Teams for collaboration, Power Automate for workflow automation, and AWS for scalable infrastructure, offering a seamless experience for development teams to manage bugs efficiently.
<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Key Features
* Bug Reporting: Users can easily report bugs by filling out a structured form within the application, providing essential details such as bug description, severity, screenshots, and steps to reproduce.
* Ticket Tracking: Facilitates real-time tracking of bug tickets, allowing developers and managers to monitor the status of reported issues, assign tasks, and set priorities.
* Integration with Microsoft Teams: Seamless integration with Microsoft Teams enables automatic notifications and updates on bug ticket status changes, ensuring effective communication among team members.
* Power Automate Workflows: Automates repetitive tasks and workflows using Power Automate, streamlining processes such as bug assignment, notification delivery, and status updates.
* AWS Cloud Infrastructure: Hosted on AWS, offering scalability, reliability, and security, ensuring high availability and performance for handling bug tracking operations.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

* [![Flask][Flask.com]][Flask-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/Jordan527/TSI-Ticketing-System.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Use an SQS queue
- [ ] Add Lambda functions 
- [ ] Send tickets to their relevant destinations
    - [ ] High priority to a slack channel
    - [ ] Medium priority to a trello board
    - [ ] Low priority to a s3 bucket

See the [open issues](https://github.com/Jordan527/TSI-Ticketing-System/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.md` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [othneildrew README template](https://github.com/othneildrew/Best-README-Template/tree/master)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/Jordan527/TSI-Ticketing-System.svg?style=for-the-badge
[contributors-url]: https://github.com/Jordan527/TSI-Ticketing-System/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Jordan527/TSI-Ticketing-System.svg?style=for-the-badge
[forks-url]: https://github.com/Jordan527/TSI-Ticketing-System/network/members
[stars-shield]: https://img.shields.io/github/stars/Jordan527/TSI-Ticketing-System.svg?style=for-the-badge
[stars-url]: https://github.com/Jordan527/TSI-Ticketing-System/stargazers
[issues-shield]: https://img.shields.io/github/issues/Jordan527/TSI-Ticketing-System.svg?style=for-the-badge
[issues-url]: https://github.com/Jordan527/TSI-Ticketing-System/issues
[license-shield]: https://img.shields.io/github/license/Jordan527/TSI-Ticketing-System.svg?style=for-the-badge
[license-url]: https://github.com/Jordan527/TSI-Ticketing-System/blob/master/LICENSE.txt

[product-screenshot]: images/screenshot.png

[Flask.com]: https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/en/3.0.x/
