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
      <a href="#setup">Setup</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#step-1-create-a-new-team-in-ms-teams">Step 1. Create a new team in MS Teams</a></li>
        <li><a href="#step-2-add-required-apps-to-ms-teams">Step 2. Add required Apps to MS Teams</a></li>
        <li><a href="#step-3-create-an-ngrok-account">Step 3. Create an Ngrok account</a></li>
        <li><a href="#step-4-build-a-power-automate-solution">Step 4. Build a Power Automate Solution</a></li>
      </ul>
    </li>
    <li>
      <a href="#aws-configuration">AWS Configuration</a>
      <ul>
        <li><a href="#iam-user">IAM User</a></li>
        <li><a href="#aws-configure">AWS Configure</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

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



<!-- SETUP -->
## Setup

To get run your own version of the TSI Ticketing System, follow the instructions below.

### Prerequisites

1. Python `pip` install the following libraries.
* `Flask`
  ```sh
  pip install flask
  ```
* `boto3`
  ```sh
  pip install boto3
  ```

Alternatively, use the following command:
```sh
pip install -r requirements.txt
```

### Step 1. Create a new team in MS Teams
1. Click the `+` button on the Teams tab of MS Teams and select `Create team`.
2. Select `From scratch` > `Public`, then give your new team a name and description, and click `Create`.
3. Create a new channel in the team by clicking the ellipsis button next to the team name, then `Add channel`.
4. Give the channel a name and select `Standard access`.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Step 2. Add required Apps to MS Teams
Click the ellipsis button on the left bar and search for `Developer Portal` and add this to teams (right-click to pin the app to the left bar).


<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Step 3. Create an Ngrok account.
1. Go to [https://ngrok.com/](https://ngrok.com/) and sign up
2. Follow the installation steps.
3. In the `Deploy your app online` section, select the second tab `Static Domain`.
4. Click the link to claim your free static domain, and save the command presented, it should look like this: `ngrok http --domain=your-domain-name.ngrok-free.app 80`

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Step 4. Build a Power Automate Solution.

1.  Navigate to [Power Automate Solutions](https://make.powerautomate.com).
2.  Click `+ New solution` at the top left of the screen, fill in the fields and click `Create`.
3.  Create the first workflow.
    1. In the solution click `+ New` > `Automation` > `Cloud flow` > `Instant`.
    2. Search for and select `Manually trigger a flow` as your trigger from Power Automate.
       1. Leave the inputs blank.
    3. Click the `+` button, search for and add `Post card in a chat or channel`.
       1. Select the `Post As` field to be `Flow bot`.
       2. Select the `Post In` field to be `Channel`.
       3. Select the `Team` field to be the team you set up in step 1.
       4. Select the `Channel` field to be the channel you set up in step 1.
       5. Paste the json from `TSI Ticket.json` into the `Adaptive Card` field.
       6. Click `Show all` advanced parameters.
       7. Give an ID to your card and put in into the `Card Type ID` field.
    4. Save this workflow.
4.  Create the second workflow.
    1. In the solution click `+ New` > `Automation` > `Cloud flow` > `Automated`.
    2. Search for and select `When someone responds to an adaptive card` as your trigger from MS Teams.
       1. Paste the json from `TSI Ticket.json` into the `Inputs Adaptive Card` field.
       2. Use the same ID used in the first workflow in the `Card Type Id` field.
    3. Click `+ New step` and search for, then select `HTTP`.
       1. Select the `Method` field to be `POST`.
       2. Paste your free static domain name from ngrok with an `https://` in front in the `URL` field.
          1. The whole URL should look like this: `https://your-domain-name.ngrok-free.app/`
       3. Click the `Switch Headers to text mode` button on the right of the `Headers` section and paste in the following headers:
          ```json
          {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Host": "your-domain-name.ngrok-free.app",
            "User-Agent": "PowerAutomateWorkflow",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
          }
          ```
       4. Make sure to replace `your-domain-name` with your actual domain name.
       5. Paste the following into the `Body` field:
          ```json
          {
              "title": <dynamic-data>,
              "description": <dynamic-data>,
              "priority": <dynamic-data>
          }
          ```
       6. Replace `<dynamic-data>` with dynamic data from `When someone responds to an adaptive card` called `title`, `description`, and `priority`.
    4. Click `+ New step` and search for, then select `Reply with a message in a channel`.
       1. Leave `Post as` field to be `Flow bot`.
       2. Select the `Post in` field to be `Chat with Flow bot`.
       3. Select the `Recipient` field to be dynamic data of `Responder User ID` from `When someone responds to an adaptive card`.
       4. Write a message in the `Message` field using the link variable to link to the message and the body dynamic data to get the response body.
    5. Save this workflow.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## AWS Configuration

### IAM User
1. Open the AWS Management Console and navigate to `IAM`.
2. Select `Users` on the left panel then click `Create user`.
3. Enter a name like `Ticket queuer` and click `Next`.
4. Under permissions keep the `Add user to group` option selected.
5. Under `User groups` create a new user group.
   1. Add a name for the user group like `TicketQueuer`.
   2. Search and select the permission policy called `AmazonSQSFullAccess`.
   3. Select `Create user group` to create the group.
6. Select your newly created user group and click `Next`.
7. Click `Create user` to create the IAM user.
8. Under the `Security credentials` tab and `Access keys` section, click `Create access key`.
   1. Select `Local code`, tick the confirmation box and click `Next`.
   2. Click `Create access key`.
   3. Save both the public and private access keys somewhere safe, not in plain text.

### AWS Configure

1. Download AWS CLI from [https://aws.amazon.com/cli/](https://aws.amazon.com/cli/).
2. Run the command `aws configure` in a terminal and complete the steps (choose a region that is close to you for minimum latency).


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
