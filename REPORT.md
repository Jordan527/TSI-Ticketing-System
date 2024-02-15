## The Problem
In many organizations, the management of issue tickets is a crucial aspect of maintaining operational efficiency and customer satisfaction. However, when all issue tickets are directed to the same location irrespective 
of their priority, it can lead to systemic problems that affect various aspects of the organization. This centralized ticket routing system, while seemingly straightforward, can result in priority blindness, 
where urgent issues get buried under a pile of lower priority tickets, leading to delays, increased resolution times, and ultimately, dissatisfied customers.

## The Approach
The overall approach to solve this problem was the set up a priority based ticket, where customers can submit a ticket with a title, priority level and description. The ticket should then have its format verified and be 
sent for resolution.

The ticket input will be hosted on Microsoft Teams for the convenience of the end users, as it is a common communication tool in the workplace. An outgoing webhook will be created, that the customer can reference to submit their 
ticket to the server.

Python Flask will be used to handle API calls and handle priority based redirects for resolution. High priority tickets will be sent to a Slack channel, medium priority tickets will be sent to a Trello board 
and low priority tickets will be sent to an AWS s3 bucket.

AWS SQS will be used to decouple the solutions architecture and will have different queues for each level of priority. Within the python code, the boto3 library will be used to create messages to SQS after determining 
which queue should be used.

## Challenges Encountered
### Webhooks
When trying to use the outgoing webhook in Microsoft Teams, it was discovered that they could not be linked to adaptive cards for use besides openURLs which would not suit the desired implementation of the solution. The only
discovered way to use the webhook for this implemntation, would be for the customer to mention the webhook and submit the ticket in free text like below:
```
@<webhook name>
Title: Lost password
Priority: Medium
Description: I lost my password and can't login
```
While using this approach would work, the following problems were encountered:
* Ensuring the user entered the title, priority and description is difficult as there is no pre-defined format with free text input
* There will always be the possibility of a typo when entering one of the field titles, causing the user to have to enter the data again
* extracting the data was difficult as the message comes through in html rather than plain text
* As priority is based on high, medium and low, it is easy for the user's input to fall outside of the allowed format with a free text input

## Solutions Implemented
### Power Automate
It was discovered that Power Automate workflows would allow the user to enter their data into an adaptive card and the data can be sent to the server via an http request rather than a webhook. While this solution required 
significantly more work, such as creating an adaptive card and Power Automate workflows, it solved all problems encountered with the original webhook approach.
* Adaptive cards to have clearly defined fields for users to enter their issue
  * Priority field is multiple choice 
  * Built in input validation to confirm all fields are filled removes the chance of user oriented errors
  * Requires less server processing so the solution will be able to handle a higher frequency of tickets before performance begins to suffer 
* HTTP post in Power Automate with a json format for easy data extraction in python
