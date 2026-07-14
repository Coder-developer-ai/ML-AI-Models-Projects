from pathlib import Path
import pypandoc

outdir=Path('/mnt/data/2025_Jan_Daily_Notes_Part1')
outdir.mkdir(exist_ok=True)

notes=[
("2025-01-01","Started the new year by cleaning my room and making a list of goals. I want to exercise more, read one book every month, and improve my cooking. Had dinner with my parents and watched the New Year celebrations on TV."),
("2025-01-02","Went back to work after the holiday. There were many emails to clear. Had lunch with Rahul, who suggested trying a new coffee shop near the office next week. Felt a little tired by the evening."),
("2025-01-03","Worked on a project report for most of the day. Took a short walk after dinner to get some fresh air. Called my sister and talked about planning a family trip later this year."),
("2025-01-04","Did grocery shopping in the morning and bought vegetables, rice, milk, and coffee. Organized the kitchen and watched a movie at home before bed."),
("2025-01-05","Woke up late and made pancakes for breakfast. Read a few chapters of a mystery novel and prepared meals for the coming workweek."),
("2025-01-06","The office was busy with meetings. Finished an important presentation before the deadline. Drank more coffee than usual because I didn't sleep well."),
("2025-01-07","Visited the new coffee shop with Rahul after work. The cappuccino was good, but the place was crowded. Reached home later than usual."),
("2025-01-08","Started exercising again with a 30-minute morning walk. Felt more energetic throughout the day. Ordered dinner because work finished late."),
("2025-01-09","Received positive feedback from my manager on last week's presentation. Paid the electricity and internet bills in the evening."),
("2025-01-10","Met a few college friends for dinner after work. We talked about our careers and shared old memories."),
("2025-01-11","Spent the morning cleaning the apartment and doing laundry. Bought a small indoor plant and cooked pasta for dinner."),
("2025-01-12","Visited my parents for lunch. My mother packed homemade snacks for me. Planned tasks for the upcoming week and read another chapter of my book.")
]

for i,(date,text) in enumerate(notes,1):
    md=f"# Daily Note\n\n**Date:** {date}\n\n{text}\n"
    outfile=outdir/f"Day_{i:02d}_{date}.txt"
    pypandoc.convert_text(md,'plain',format='md',outputfile=str(outfile),extra_args=['--standalone'])
print(outdir)
