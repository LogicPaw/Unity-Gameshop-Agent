using System.Collections.Generic;
using UnityEngine;

public class CsvOfferLoader : MonoBehaviour
{
    public TextAsset csvFile;

    void Start()
    {
        List<OfferData> offers = ParseCsv(csvFile);

        foreach (OfferData offer in offers)
        {
            Debug.Log(offer);
        }
    }

    List<OfferData> ParseCsv(TextAsset csv)
    {
        List<OfferData> result = new List<OfferData>();

        string[] lines = csv.text.Split('\n');

        // 第 0 行是表头，所以从第 1 行开始
        for (int i = 1; i < lines.Length; i++)
        {
            string line = lines[i].Trim();

            if (string.IsNullOrEmpty(line))
                continue;

            string[] columns = line.Split(',');

            OfferData offer = new OfferData();

            offer.offer_id = columns[0].Trim();
            offer.display_name = columns[1].Trim();
            offer.category = columns[2].Trim();
            offer.reward_id = columns[3].Trim();

            int.TryParse(columns[4].Trim(), out offer.reward_amount);

            offer.cost_id = columns[5].Trim();

            int.TryParse(columns[6].Trim(), out offer.cost_amount);

            offer.badge_text = columns[7].Trim();

            bool.TryParse(columns[8].Trim(), out offer.enabled);

            result.Add(offer);
        }

        return result;
    }
}
