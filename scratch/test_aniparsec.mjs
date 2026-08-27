import { AniParsec } from 'aniparsec-ru';

async function main() {
  const parser = new AniParsec();
  console.log("Searching for Brotherhood...");
  const results = await parser.search('Fullmetal Alchemist Brotherhood');
  
  if (results.length > 0) {
    const first = results[0];
    console.log("Found:", first.title, "ID:", first.id);
    
    console.log("Getting translations...");
    const trans = await parser.getTranslations(first.id);
    console.log("Translations found:", trans.length);
    if (trans.length > 0) {
        console.log("First 3 trans:", trans.slice(0, 3));
        
        console.log("Getting video for Ep 1, Trans 0...");
        try {
            const video = await parser.getVideo({
                shikimoriId: first.id,
                episode: 1,
                translationId: trans[0].id
            });
            console.log("Video URL:", video.url);
        } catch (e) {
            console.error("Failed to get video:", e.message);
        }
    }
  } else {
    console.log("No results");
  }
}

main().catch(console.error);
