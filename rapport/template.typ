// Gabarit commun des documents remis à l'enseignant (rapport, état de l'art, notes).

#let rapport(
  course: "SAE M2 DFS & DE",
  title: "Titre",
  subtitle: none,
  authors: (),
  date: none,
  lang: "fr",
  unbreakable-tables: true,  // false for documents with long tables
  body,
) = {
  set document(title: title, author: authors)
  set text(font: "New Computer Modern", size: 11pt, lang: lang)
  set par(justify: true)
  set heading(numbering: "1.1", supplement: "Section")
  show heading.where(level: 1): it => {
    v(0.8em)
    it
    v(0.3em)
  }
  set table(stroke: 0.4pt + luma(160), inset: 6pt)
  show table: set par(justify: false)
  show table: set text(size: 10pt)
  show table: it => if unbreakable-tables { block(breakable: false, it) } else { it }
  show bibliography: set text(size: 8.5pt)
  show bibliography: set block(spacing: 0.35em)
  show table.cell.where(y: 0): set text(weight: "bold")
  set page(
    paper: "a4",
    margin: 2cm,
    header: context {
      if counter(page).get().first() > 1 [
        #set text(9pt)
        #course #h(1fr) #title
        #line(length: 100%, stroke: 0.4pt)
      ]
    },
    numbering: "1 / 1",
  )

  align(center)[
    #text(9pt, upper(course)) \
    #v(0.2em)
    #text(18pt, weight: "bold", title) \
    #if subtitle != none [ #v(0.1em) #text(12pt, subtitle) \ ]
    #v(0.4em)
    #authors.join(", ")
    #if date != none [ \ #text(9pt, date) ]
  ]
  line(length: 100%, stroke: 0.6pt)
  v(0.8em)

  body
}

// Encadré pour un point clé ou une limite à retenir.
#let note(title: "À retenir", body) = block(
  width: 100%,
  inset: 10pt,
  radius: 3pt,
  stroke: (left: 2pt + rgb("#4a6fa5")),
  fill: rgb("#f3f6fb"),
)[
  #text(weight: "bold", fill: rgb("#4a6fa5"))[#title.] #body
]
