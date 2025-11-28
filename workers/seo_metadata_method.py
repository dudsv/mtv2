    def _add_seo_metadata_table(self, doc, soup):
        """Add SEO metadata table at the end of the document."""
        try:
            # Add section header
            header = doc.add_paragraph()
            run = header.add_run("SEO METADATA")
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 112, 192)
            
            # Extract metadata
            meta_title = soup.find('title')
            meta_title_text = meta_title.string.strip() if meta_title and meta_title.string else "No Meta Title"
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_desc_text = meta_desc.get('content', 'No Meta Description') if meta_desc else "No Meta Description"
            
            og_title = soup.find('meta', property='og:title')
            og_title_text = og_title.get('content', 'No OG Title') if og_title else "No OG Title"
            
            og_desc = soup.find('meta', property='og:description')
            og_desc_text = og_desc.get('content', 'No OG Description') if og_desc else "No OG Description"
            
            schemas = soup.find_all('script', type='application/ld+json')
            if schemas:
                schema_texts = [s.string.strip() for s in schemas if s.string]
                schema_text = "\n---\n".join(schema_texts)
                # Truncate if too long
                if len(schema_text) > 1000:
                    schema_text = schema_text[:1000] + "...[truncated]"
            else:
                schema_text = "No Schema"
            
            # Create table with 5 columns
            table = doc.add_table(rows=2, cols=5)
            table.style = 'Light Grid Accent 1'
            
            # Header row
            headers = ['Meta Title', 'Meta Description', 'OG Title', 'OG Description', 'Schema']
            for i, header_text in enumerate(headers):
                cell = table.rows[0].cells[i]
                p = cell.paragraphs[0]
                run = p.add_run(header_text)
                run.bold = True
            
            # Data row
            data = [meta_title_text, meta_desc_text, og_title_text, og_desc_text, schema_text]
            for i, value in enumerate(data):
                table.rows[1].cells[i].text = value
                
        except Exception as e:
            self.log_update.emit(f"Error adding SEO metadata table: {e}")
