# -*- coding: utf-8 -*-
import scrapy


class IndeedSpider(scrapy.Spider):
    name = 'indeed'
    allowed_domains = ['www.indeed.com']
    start_urls = ['https://www.indeed.com/Top-Rated-Workplaces']

    def parse(self, response):
        list_top_companies = response.css('ul#cmp-discovery-curated-list li a::attr(href)').extract()
        for category in list_top_companies:
            link = response.urljoin(category)
            yield scrapy.Request(link, callback=self.parse_companies)

    def parse_companies(self, response):
        companies = response.css('.cmp-company-tile-with-footer .cmp-company-tile-name a::attr(href)').extract()
        for company in companies:
            link = response.urljoin(company) + '/reviews'
            yield scrapy.Request(link, callback=self.parse_reviews)

        links = response.css('.cmp-paginator-page')
        for next_link in links:
            if next_link.css('::attr(data-tn-element)').extract_first() == 'next-page':
                next_link = next_link.css('::attr(href)').extract_first()
                next_link = response.urljoin(next_link)
                yield scrapy.Request(next_link, callback=self.parse_companies)

    def parse_reviews(self, response):
        item = {}
        company_name = response.css('.cmp-company-name::text').extract_first()

        reviews = response.css('.cmp-review')
        for review in reviews:
            rating = review.css('.cmp-ratingNumber::text').extract_first()
            sub_ratings = review.css('.cmp-ratings-expanded')
            sub_ratings_list = []
            for sub_rating in sub_ratings.css('tr'):
                cat = sub_rating.css('td::text').extract_first()
                width = sub_rating.css('.cmp-star-cell .cmp-Rating-on::attr(style)').re_first('width: (\d+)')
                stars = 0
                if int(width) == 20:
                    stars = 1
                elif int(width) == 40:
                    stars = 2
                elif int(width) == 60:
                    stars = 3
                elif int(width) == 80:
                    stars = 4
                elif int(width) == 100:
                    stars = 5
                sub_ratings_list.append((cat, stars))

            sub_ratings = sub_ratings_list

            review_title = review.css('.cmp-review-title span::text').extract_first()
            employee_designation = review.css('.cmp-reviewer-job-title ::text').extract_first()
            location = review.css('.cmp-reviewer-job-location::text').extract_first()
            date = review.css('.cmp-review-date-created::text').extract_first()
            review_text = review.css('.cmp-review-description .cmp-review-text::text').extract_first()

            item['company_name'] = company_name
            item['rating'] = rating
            item['sub_ratings'] = sub_ratings
            item['review_title'] = review_title
            item['employee_designation'] = employee_designation
            item['location'] = location
            item['date'] = date
            item['review_text'] = review_text
            pros = ''
            cons = ''
            if review.css('.cmp-review-pros-cons-content'):
                pros = review.css('.cmp-review-pro-text::text').extract_first()
                cons = review.css('.cmp-review-con-text::text').extract_first()
            item['pros'] = pros
            item['cons'] = cons

            yield item

        links = response.css('.cmp-Pagination-link--nav')
        for link in links:
            if link.css('::attr(data-tn-element)').extract_first() == 'next-page':
                next_link = link.css('::attr(href)').extract_first()
                next_link = response.urljoin(next_link)
                yield scrapy.Request(next_link, callback=self.parse_reviews)
