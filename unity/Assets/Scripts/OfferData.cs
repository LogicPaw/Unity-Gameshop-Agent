using System;

[Serializable]
public class OfferData
{
    public string offer_id;
    public string display_name;
    public string category;
    public string reward_id;
    public int reward_amount;
    public string cost_id;
    public int cost_amount;
    public string badge_text;
    public bool enabled;

    public override string ToString()
    {
        return $"Offer ID: {offer_id}, " +
               $"Name: {display_name}, " +
               $"Reward: {reward_id} x{reward_amount}, " +
               $"Cost: {cost_id} x{cost_amount}, " +
               $"Enabled: {enabled}";
    }
}
