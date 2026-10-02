# Retrieval eval

mode=`vector` · k=3 · MIN_SIMILARITY=0.224 · chunks 350/50 · `openai:text-embedding-3-small`

- Hit rate@3: 39/40 = 98%
- MRR@3:      0.850
- Top-1 similarity, answerable:   min 0.254  avg 0.433
- Top-1 similarity, unanswerable: max 0.652  avg 0.429
- Unanswerable refused by threshold 0.224: 1/10 (the LLM prompt is a second guard; see eval_answers.py)
- Best separating threshold on this data: 0.283 (84% accuracy)

```
  1  ✓       3    0.337  What operating systems does the desktop app support?
  2  ✓       2    0.520  Can I create a new pool from my phone?
  3  ✓       1    0.394  How many columns can a pool have?
  4  ✗       -    0.311  What happens to tasks nobody has touched in a month?
  5  ✓       1    0.390  What is the keyboard shortcut to only show tasks assigned to
  6  ✓       1    0.454  Is there a limit on how many tasks I can import from Trello 
  7  ✓       1    0.432  How much does the Current plan cost if I pay monthly?
  8  ✓       1    0.435  What is the minimum number of seats for Riptide?
  9  ✓       1    0.318  Do nonprofits get a discount?
 10  ✓       1    0.489  How long is the free trial and do I need a credit card?
 11  ✓       1    0.254  Can I pay with PayPal?
 12  ✓       2    0.473  Will I get a refund if I cancel my annual plan after two mon
 13  ✓       1    0.368  What happens if my card payment keeps failing?
 14  ✓       1    0.492  Can I store my workspace data in Europe?
 15  ✓       1    0.363  Does two-factor authentication support SMS codes?
 16  ✓       2    0.404  How long are deleted tasks kept before they are gone for goo
 17  ✓       2    0.469  How often are backups taken and how long are they kept?
 18  ✓       1    0.422  What is the API rate limit per token?
 19  ✓       1    0.523  How do I verify that a webhook request really came from Tide
 20  ✓       1    0.405  What is the maximum page size when listing ripples through t
 21  ✓       1    0.508  How many Slack channels can one pool be linked to?
 22  ✓       1    0.475  What happens to a ripple when its linked pull request is mer
 23  ✓       1    0.404  If I move a ripple's event in Google Calendar, does the due 
 24  ✓       1    0.470  Do Zapier zaps count toward the Free plan integration limit?
 25  ✓       2    0.502  Can people outside my team email tasks into a pool?
 26  ✓       1    0.518  How many automations can a pool have on the Free plan?
 27  ✓       1    0.478  What happens when we hit the monthly automation run limit?
 28  ✓       1    0.428  Can automation conditions use OR?
 29  ✓       1    0.486  How do automations avoid infinite loops?
 30  ✓       1    0.541  What time are recurring ripples created?
 31  ✓       3    0.413  How long is automation history kept on paid plans?
 32  ✓       2    0.394  How long are member invitations valid?
 33  ✓       1    0.346  What happens to a deactivated member's assigned tasks?
 34  ✓       1    0.599  How do I hand over ownership of the workspace to someone els
 35  ✓       1    0.475  How long does a workspace export download link stay valid?
 36  ✓       1    0.460  Can a deleted workspace be restored?
 37  ✓       1    0.580  How many custom fields can a pool have?
 38  ✓       1    0.311  How many times is a failed webhook delivery retried?
 39  ✓       1    0.296  When was the Australia data region added?
 40  ✓       3    0.401  What was the API rate limit before it was raised to 120?
 41  LEAK  n/a    0.652  Does Tidepool integrate with Microsoft Teams?
 42  LEAK  n/a    0.487  Is Tidepool SOC 2 certified?
 43  LEAK  n/a    0.543  Can I self-host Tidepool on my own servers?
 44  LEAK  n/a    0.614  Who founded Tidepool and when?
 45  LEAK  n/a    0.227  What is the phone number for customer support?
 46  LEAK  n/a    0.371  What is the maximum length of a ripple title?
 47  LEAK  n/a    0.545  Which languages is the Tidepool interface available in?
 48  LEAK  n/a    0.536  Does Tidepool offer a Gantt chart or timeline view?
 49  IDK   n/a    0.039  What is the capital of Peru?
 50  LEAK  n/a    0.270  How do I reset my password if I lose access to my email?
```
