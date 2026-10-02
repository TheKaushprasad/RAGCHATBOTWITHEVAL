# Retrieval eval

mode=`vector` · k=5 · MIN_SIMILARITY=0.3 · chunks 500/50 · `openai:text-embedding-3-small`

- Hit rate@5: 39/40 = 98%
- MRR@5:      0.790
- Top-1 similarity, answerable:   min 0.259  avg 0.416
- Top-1 similarity, unanswerable: max 0.638  avg 0.432
- Unanswerable refused by threshold 0.3: 3/10 (the LLM prompt is a second guard; see eval_answers.py)
- Best separating threshold on this data: 0.248 (86% accuracy)

```
  1  ✓       3    0.280  What operating systems does the desktop app support?
  2  ✓       1    0.477  Can I create a new pool from my phone?
  3  ✓       1    0.399  How many columns can a pool have?
  4  ✗       -    0.337  What happens to tasks nobody has touched in a month?
  5  ✓       2    0.285  What is the keyboard shortcut to only show tasks assigned to
  6  ✓       1    0.398  Is there a limit on how many tasks I can import from Trello 
  7  ✓       1    0.406  How much does the Current plan cost if I pay monthly?
  8  ✓       1    0.468  What is the minimum number of seats for Riptide?
  9  ✓       1    0.305  Do nonprofits get a discount?
 10  ✓       1    0.427  How long is the free trial and do I need a credit card?
 11  ✓       1    0.266  Can I pay with PayPal?
 12  ✓       1    0.423  Will I get a refund if I cancel my annual plan after two mon
 13  ✓       1    0.292  What happens if my card payment keeps failing?
 14  ✓       3    0.487  Can I store my workspace data in Europe?
 15  ✓       1    0.259  Does two-factor authentication support SMS codes?
 16  ✓       1    0.394  How long are deleted tasks kept before they are gone for goo
 17  ✓       1    0.497  How often are backups taken and how long are they kept?
 18  ✓       1    0.397  What is the API rate limit per token?
 19  ✓       2    0.511  How do I verify that a webhook request really came from Tide
 20  ✓       1    0.427  What is the maximum page size when listing ripples through t
 21  ✓       1    0.478  How many Slack channels can one pool be linked to?
 22  ✓       4    0.453  What happens to a ripple when its linked pull request is mer
 23  ✓       2    0.350  If I move a ripple's event in Google Calendar, does the due 
 24  ✓       1    0.504  Do Zapier zaps count toward the Free plan integration limit?
 25  ✓       5    0.465  Can people outside my team email tasks into a pool?
 26  ✓       2    0.560  How many automations can a pool have on the Free plan?
 27  ✓       2    0.564  What happens when we hit the monthly automation run limit?
 28  ✓       1    0.418  Can automation conditions use OR?
 29  ✓       2    0.506  How do automations avoid infinite loops?
 30  ✓       1    0.498  What time are recurring ripples created?
 31  ✓       1    0.575  How long is automation history kept on paid plans?
 32  ✓       2    0.355  How long are member invitations valid?
 33  ✓       1    0.308  What happens to a deactivated member's assigned tasks?
 34  ✓       1    0.519  How do I hand over ownership of the workspace to someone els
 35  ✓       1    0.534  How long does a workspace export download link stay valid?
 36  ✓       1    0.434  Can a deleted workspace be restored?
 37  ✓       2    0.401  How many custom fields can a pool have?
 38  ✓       1    0.337  How many times is a failed webhook delivery retried?
 39  ✓       1    0.273  When was the Australia data region added?
 40  ✓       2    0.370  What was the API rate limit before it was raised to 120?
 41  LEAK  n/a    0.638  Does Tidepool integrate with Microsoft Teams?
 42  LEAK  n/a    0.536  Is Tidepool SOC 2 certified?
 43  LEAK  n/a    0.554  Can I self-host Tidepool on my own servers?
 44  LEAK  n/a    0.608  Who founded Tidepool and when?
 45  IDK   n/a    0.237  What is the phone number for customer support?
 46  LEAK  n/a    0.385  What is the maximum length of a ripple title?
 47  LEAK  n/a    0.567  Which languages is the Tidepool interface available in?
 48  LEAK  n/a    0.562  Does Tidepool offer a Gantt chart or timeline view?
 49  IDK   n/a    0.054  What is the capital of Peru?
 50  IDK   n/a    0.179  How do I reset my password if I lose access to my email?
```
