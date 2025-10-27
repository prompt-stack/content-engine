import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import fs from 'fs/promises';

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36';

const games = [
  { url: 'https://www.pro-football-reference.com/boxscores/202509080chi.htm', week: 1 },
  { url: 'https://www.pro-football-reference.com/boxscores/202509140det.htm', week: 2 },
  { url: 'https://www.pro-football-reference.com/boxscores/202509210chi.htm', week: 3 },
  { url: 'https://www.pro-football-reference.com/boxscores/202509280rai.htm', week: 4 },
  { url: 'https://www.pro-football-reference.com/boxscores/202510130was.htm', week: 6 },
  { url: 'https://www.pro-football-reference.com/boxscores/202510190chi.htm', week: 7 }
];

async function extractPlayByPlay(url) {
  console.error(`Fetching ${url}...`);

  const response = await fetch(url, {
    headers: { 'User-Agent': USER_AGENT }
  });

  let html = await response.text();

  // Uncomment hidden tables (Pro Football Reference technique)
  html = html.replace(/<!--([\s\S]*?)-->/g, '$1');

  const $ = cheerio.load(html);

  // Get team abbreviations from the URL or page
  const pbpTable = $('#pbp');

  if (pbpTable.length === 0) {
    throw new Error('Play-by-play table not found');
  }

  // Get team abbreviations from first data row
  let awayTeam = '';
  let homeTeam = '';

  const firstRow = pbpTable.find('thead tr').first();
  const headers = [];
  firstRow.find('th').each((i, th) => {
    const abbr = $(th).attr('data-stat');
    const text = $(th).text().trim();
    if (abbr && abbr.includes('team_score')) {
      if (abbr.includes('away')) awayTeam = text;
      if (abbr.includes('home')) homeTeam = text;
    }
  });

  const plays = [];

  // Extract all plays
  pbpTable.find('tbody tr').each((i, row) => {
    const $row = $(row);

    const quarter = $row.find('[data-stat="quarter"]').text().trim();
    const time = $row.find('[data-stat="quarter_seconds_left"]').text().trim();
    const down = $row.find('[data-stat="down"]').text().trim();
    const togo = $row.find('[data-stat="yds_to_go"]').text().trim();
    const location = $row.find('[data-stat="location"]').text().trim();
    const awayScore = $row.find('[data-stat="away_team_score"]').text().trim();
    const homeScore = $row.find('[data-stat="home_team_score"]').text().trim();
    const detail = $row.find('[data-stat="detail"]').text().trim();
    const epb = $row.find('[data-stat="pbp_score_aw"]').text().trim();
    const epa = $row.find('[data-stat="pbp_score_hm"]').text().trim();

    if (!detail && !time) return; // Skip empty rows

    plays.push({
      Quarter: quarter,
      Time: time,
      Down: down,
      ToGo: togo,
      Location: location,
      [awayTeam]: awayScore,
      [homeTeam]: homeScore,
      Detail: detail,
      EPB: epb,
      EPA: epa
    });
  });

  return { plays, awayTeam, homeTeam };
}

function convertToCSV(plays, awayTeam, homeTeam) {
  if (plays.length === 0) return '';

  // CSV Header
  const headers = ['Quarter', 'Time', 'Down', 'ToGo', 'Location', awayTeam, homeTeam, 'Detail', 'EPB', 'EPA'];
  const csvLines = [headers.join(',')];

  // CSV Rows
  plays.forEach(play => {
    const row = headers.map(header => {
      const value = play[header] || '';
      // Escape commas and quotes in detail field
      if (header === 'Detail' && value) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    });
    csvLines.push(row.join(','));
  });

  return csvLines.join('\n');
}

async function main() {
  const outputDir = '/Users/hoff/Desktop/My Drive/content/topics/personal/nfl/bears';

  for (const game of games) {
    try {
      console.error(`\n=== Processing Week ${game.week} ===`);

      const { plays, awayTeam, homeTeam } = await extractPlayByPlay(game.url);
      console.error(`Extracted ${plays.length} plays`);

      const csv = convertToCSV(plays, awayTeam, homeTeam);

      const outputPath = `${outputDir}/week${game.week}_play.csv`;
      await fs.writeFile(outputPath, csv);

      console.error(`✓ Saved to ${outputPath}\n`);

      // Delay between requests to be polite
      await new Promise(resolve => setTimeout(resolve, 2000));

    } catch (error) {
      console.error(`✗ Error processing week ${game.week}: ${error.message}\n`);
    }
  }

  console.error('Done!');
}

main().catch(console.error);
