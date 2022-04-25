// Register a template definition set named "default".
CKEDITOR.addTemplates( 'default',
{
  // The name of the subfolder that contains the preview images of the templates.
  imagesPath : CKEDITOR.getUrl( CKEDITOR.plugins.getPath( 'templates' ) + 'templates/images/' ),

  // Template definitions.
  templates :
    [
      {
        title: 'Well - Standard',
        image: 'template1.gif',
        description: 'Use the well on an element to give it an inset effect.',
        html:
          '<div class="well">' +
              '<h2 class="headline-underline">Featured Content Header</h2>' +
              '<h3>SUB-HEADER EXAMPLE</h3>' +
              '<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididuntut labore et dolore magna aliqua, consectetur adipisicing elit, sed do eiusmod.</p>' +
          '</div>'
      },

      {
        title: 'Well - With Image',
        image: 'template1.gif',
        description: 'A well with an image contained inside. Uses bootstrap grid classes to establish columns.',
        html:

          '<div class="well">' +
            '<h2 class="headline-underline">Featured Content Header Example</h2>' +
            '<div class="row">' +
              '<div class="col-xs-12 col-sm-3">' +
                '<img src="http://placehold.it/400x400" alt="" class="img-responsive">' +
              '</div>' +
              '<div class="col-xs-12 col-sm-9">' +
                '<h3>Sub-header Example</h3>' +
                '<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididuntut labore et dolore magna aliqua, consectetur adipisicing elit, sed do eiusmod.</p>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Image Block With Caption',
        image: 'template1.gif',
        description: 'A full width image block with a caption included',
        html:

          '<div class="image-block">' +
              '<img src="//placehold.it/1000x400" />' +
              '<div class="caption">' +
                '<p><b>Example Caption:</b> Replace this text</p>' +
              '</div>' +
          '</div>'
      },

      {
        title: 'Pull Quote (Blockquote with Border)',
        image: 'template1.gif',
        description: 'This is a called out quote taken from the page content. It is signified by a vertical blue line on the left side.',
        html:

          '<blockquote class="border-on-left">Blockquote text here...</blockquote>'

      },

      {
        title: 'Full Width Zone',
        image: 'template1.gif',
        description: 'A single, full width implementation of LayoutTracery',
        html:
          '<div class="layout-tracery">' +
            '<div class="layout-column"><h2>Full Width Zone</h2><p>Content for full width zone...</p></div>' +
          '</div>'
      },

      {
        title: 'Two Column Full Width Zone',
        image: 'template1.gif',
        description: 'A balanced, two-column implementation of LayoutTracery that collapses to one column at the smallest breakpoint.',
        html:
          '<div class="layout-tracery layout-tracery-2col">' +
            '<div class="layout-column"><h2>Column Two Zone</h2><p>Content for column one zone...</p></div>' +
            '<div class="layout-column"><h2>Column One Zone</h2><p>Content for column two zone...</p></div>' +
          '</div>'
      },

      {
        title: 'Three Column Full Width Zone',
        image: 'template1.gif',
        description: 'A balanced, three-column implementation of LayoutTracery that collapses to one column at the smallest breakpoint.',
        html:
          '<div class="layout-tracery layout-tracery-3col">' +
            '<div class="layout-column"><h2>Column One Zone</h2><p>Content for column one zone...</p></div>' +
            '<div class="layout-column"><h2>Column Two Zone</h2><p>Content for column twp zone...</p></div>' +
            '<div class="layout-column"><h2>Column Three Zone</h2><p>Content for column three zone...</p></div>' +
          '</div>'
      },

      {
        title: 'Accordion',
        image: 'template1.gif',
        description: 'Accordion element',
        html:

          '<div class="accordion open">' +
            '<h2 class="accordion-handle">Accordion</h2>' +
            '<div class="accordion-content">Content for accordion...</div>' +
          '</div>'

      },

      {
        title: 'SectionIcon - Attention',
        image: 'template1.gif',
        description: 'An alert message to draw the user\'s attention to a block.',
        html:
          '<div class="section-icon section-icon-attention">' +
            '<h3>IMPORTANT HEADER EXAMPLE</h3>' +
            '<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididuntut labore et dolore magna aliqua, consectetur adipisicing elit, sed do eiusmod.</p>' +
          '</div>'
      },

      // {
      //  title: 'CM Text',
      //  image: 'template1.gif',
      //  description: 'Inline text to display the number of cm credits for events',
      //  html:
      //    '<span class="cm-wrapper">' +
    //                   '<span class="cm">CM | </span><span class="cmpoints">##</span>' +
    //               '</span>'
      // },

      {
        title: 'Address',
        image: 'template1.gif',
        description: 'A paragraph element used to display a street address.',
        html:
          '<p class="address">' +
                      '<span>205 N Michigan Ave</span><br/>' +
                      '<span>#1200</span><br/>' +
                      '<span>Chicago, IL 60601</span>' +
                 '</p>'
      },

      {
        title: 'Dashed Rule',
        image: 'template1.gif',
        description: 'A thicker, dashed rule.',
        html:
          '<hr class="dashed" />'
      },

      {
        title: 'Double Rule',
        image: 'template1.gif',
        description: 'A double line rule.',
        html:
          '<hr class="double" />'
      },

      {
        title: 'List of Links',
        image: 'template1.gif',
        description: 'A list of links.',
        html:
          '<div class="list-of-links">' +
            '<h4><a href="...">Example Link 1</a></h4>' +
            '<h4><a href="...">Example Link 2</a></h4>' +
            '<h4><a href="...">Example Link 2</a></h4>' +
          '</div>'
      },

      {
        title: 'Read More Link',
        image: 'template1.gif',
        description: 'A simple "read more" link for consistent styling.',
        html:
          '<a href="..." class="read-more-link">Read more</a>'
      },

      {
        title: 'Read More Link - Fancy',
        image: 'template1.gif',
        description: 'A fancy "read more" link with a graphical line rule effect.',
        html:

          '<div class="read-more-link">' +
            '<a>Read More</a>' +
          '</div>'

      },

      {
        title: 'Standalone Link',
        image: 'template1.gif',
        description: 'A link element, like the read more link, but without vertical margins.',
        html:
          '<a href="..." class="standalone-link">A link out to another page</a>'
      },

      {
        title: 'Half Inner Zone - Publications',
        image: 'template1.gif',
        description: 'For displaying publications in a half column. (Use within "Two Column Full Width Zone" template)',
        html:

          '<h2>Publication Title</h2>' +
          '<p>Some introductory text for this publication</p>' +
          '<br/>' +
          '<div class="row">' +
            '<div class="col-xs-6 col-sm-12 col-md-6">' +
              '<img class="img-responsive" src="//placehold.it/260x320">' +
            '</div>' +
            '<div class="col-xs-6 col-sm-12 col-md-6">'+
              '<h5>Secondary Title</h5>' +
              '<div class="list-of-links list-of-links-small">' +
                '<h4><a>List of links 1</a></h4>' +
                '<h4><a>List of links 2</a></h4>' +
                '<h4><a>List of links 3</a></h4>' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<div class="read-more-link"><a>Learn More</a></div>'
      },

      {
        title: 'Half Inner Zone - Events',
        image: 'template1.gif',
        description: 'For displaying events in a half column. (Use within "Two Column Full Width Zone" template)',
        html:

          '<h2>Event Title</h2>' +
          '<p>Short copy about this Event. This is a general description to help users drill down into this content.</p>' +
          '<br/>' +
          '<div class="row">' +
            '<div class="col-xs-12 col-lg-4">' +
              '<img class="img-responsive" src="//placehold.it/600x600">' +
            '</div>' +
            '<div class="col-xs-12 col-lg-8">'+
              '<p>Brief description of this Event.</p>' +
              '<h5>Secondary Title</h5>' +
              '<div class="content-preview-item">' +
                      '<h6 class="content-preview-item-superheadline">Content Preview Super Headline</h6>' +
                      '<h4 class="content-preview-item-headline"><a>Content Preview Headline</a></h4>' +
                      '<div class="content-preview-item-postline"><a>Content Preview Postline</a></div>' +
                  '</div>' +
            '</div>' +
          '</div>' +
          '<div class="read-more-link"><a>Learn More</a></div>'
      },

      {
        title: 'Image and Two Columns Zone',
        image: 'template1.gif',
        description: 'Zone spannig the entire width of the page. Image on the left and two colums for content. Use by itself (outside of any other "Zone")',
        html:

          '<div class="layout-tracery">' +
              '<div class="layout-column">' +
                '<div class="row">' +
                    '<div class="col-xs-12 col-md-4 col-lg-3">' +
                      '<img src="//placehold.it/600x600" class="img-responsive">' +
                    '</div>' +
                    '<div class="col-xs-12 col-md-8 col-lg-9">' +
                      '<h2 class="headline-underline">' +
                          '<small>October 28, 2016 | Washington DC, USA</small>' +
                          'AICP Symposiums' +
                      '</h2>' +
                      '<div class="row">' +
                          '<div class="col-xs-12 col-md-12 col-lg-7">' +
                            '<p><strong>AICP sponsors regular symposiums on a variety of topics vital to practicing planners.</strong> This years\' focus is In urban areas, stormwater presents major challenges for water quality. Runoff and combined sewer overflows result in impaired quality and degraded watersheds. Increasingly, green infrastructure approaches can treat and reduce discharge volumes and help mitigate flood risk, in addition to a range of environmental, social, and economic benefits.</p>' +
                            '<p><a href="#" class="btn btn-primary">Register Now</a></p>' +
                            '<br>' +
                          '</div>' +
                          '<div class="col-xs-12 col-md-12 col-lg-5">' +
                            '<h5>Key Speakers</h5>' +
                            '<div class="list-of-speakers">' +
                                '<h4>Paula Conolly, AICP</h4>' +
                                '<p>Policy Strategist, Green City, Clean Waters Program, Philadelphia Water Department</p>' +
                                '<h4>Bethany Bezak, PE, LEED AP</h4>' +
                                '<p>Green Infrastructure Manager, DC Water, DC Clean Rivers Project</p>' +
                                '<h4>Mathy Stanislaus</h4>' +
                                '<p>Assistant Administrator for the Office of Solid Waste and Emergency Response, U.S. EPA</p>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
              '</div>' +
                '<div class="read-more-link">' +
                  '<a href="#">Learn more about AICP Symposiums</a>' +
                '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Hero Image / Well with Image',
        image: 'template1.gif',
        description: 'A special headline used for section overview pages',
        html:
          '<div class="layout-hero-image"><img class="layout-hero-image-image" src="//placehold.it/970x370/3e3918">' +
            '<div class="layout-hero-image-content">' +
              '<h3 class="featured-item-title"><span>New from APA Planners Press</span></h3>' +
              '<div class="layout-tracery no-top-border slab-gray">' +
                '<div class="layout-column section-overview-featured-item">' +
                  '<div class="row">' +
                    '<div class="col-sm-6 col-md-4 col-lg-3"><img class="img-responsive" src="//placehold.it/240x320"></div>' +
                    '<div class="col-sm-6 col-md-8 col-lg-9">' +
                      '<h2 class="headline-underline">Rural By Design</h2>' +
                      '<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud sed do eiusmod.</p>' +
                    '</div>' +
                  '</div>' +
                  '<div class="read-more-link"><a href="#">Read more about Rural by Design</a></div>' +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Hero Image / Well Standard',
        image: 'template1.gif',
        description: 'A special headline used for section overview pages',
        html:
          '<div class="layout-hero-image"><img class="layout-hero-image-image" src="//placehold.it/970x370/3e3918">' +
            '<div class="layout-hero-image-content">' +
              '<h3 class="featured-item-title"><span>New from APA Planners Press</span></h3>' +
              '<div class="layout-tracery no-top-border slab-gray">' +
                '<div class="layout-column section-overview-featured-item">' +
                  '<h2>Featured Content Header</h2>' +
                  '<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididuntut labore et dolore magna aliqua, consectetur adipisicing elit, sed do eiusmod.</p>' +
                  '<div class="read-more-link"><a href="#">Learn More</a></div>' +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title:"Well - Image and Two Columns",
        image: 'template1.gif',
        description:'Well with image and two columns',
        html:
          '<div class="layout-tracery slab-gray">' +
            '<div class="layout-column">' +
              '<div class="row">' +
                '<div class="col-xs-12 col-sm-6 col-md-4 col-lg-3"><img class="img-responsive" src="//placehold.it/240x320"></div>' +
                '<div class="col-xs-12 col-sm-6 col-md-8 col-lg-9">' +
                  '<h2 class="headline-underline">Planning Magazine</h2>' +
                  '<div class="row">' +
                    '<div class="col-xs-12 col-md-12 col-lg-8">' +
                      '<div>' +
                        '<p>APA\'s member magazine shows how innovative planning programs and techniques are reshaping America\'s communities.</p>' +
                        '<p><a class="btn btn-primary" href="#fpo">Subscribe to Planning Magazine</a></p>' +
                      '</div>' +
                    '</div>' +
                    '<div class="col-xs-12 col-md-12 col-lg-4">' +
                      '<h5>In This Issue</h5>' +
                      '<div class="list-of-links list-of-links-small">' +
                        '<h4><a href="#fpo">A Rising Tide of Engagement</a></h4>' +
                        '<h4><a href="#fpo">Water Warrior</a></h4>' +
                        '<h4><a href="#fpo">Preparing for the Next Big One</a></h4>' +
                      '</div>' +
                    '</div>' +
                  '</div>' +
                '</div>' +
              '</div>' +
              '<div class="read-more-link"><a href="#">Learn More About The Magazine</a></div>' +
            '</div>' +
          '</div>'
      },

      {
        title: '2 Column List of Names with Modal (Currently no modal built in)',
        image: 'template1.gif',
        description: 'A section overview page pattern for a section of content in 2 columns as links.',
        html:
          '<h2 class="headline-underline">Header for List of Names...</h2>' +
          '<div class="row">' +
            '<div class="col-xs-12 col-sm-6">' +
              '<h4><a>Andre the Giant</a></h4>' +
              '<h4><a>Hulk Hogan</a></h4>' +
              '<h4><a>Stone Cold Steve Austin, AICP</a></h4>' +
              '<h4><a>...</a></h4>' +
            '</div>' +
            '<div class="col-xs-12 col-sm-6">' +
              '<h4><a>Roger Clemens</a></h4>' +
              '<h4><a>Mike Piazza</a></h4>' +
              '<h4><a>Cal Ripken jr</a></h4>' +
              '<h4><a>...</a></h4>' +
            '</div>' +
          '</div>'
      },

      {
        title: '3 Column List of Names with Modal (Currently no modal built in)',
        image: 'template1.gif',
        description: 'A section overview page pattern for a section of names in 3 columns as links.',
        html:
          '<h2 class="headline-underline">Header for List of Names...</h2>' +
          '<div class="row">' +
            '<div class="col-xs-12 col-sm-4">' +
              '<h3>A</h3>'+
              '<h4><a>Andre the Giant</a></h4>' +
              '<h3>C</h3>'+
              '<h4><a>Roger Clemens</a></h4>' +
              '<h3>H</h3>'+
              '<h4><a>George Harrison</a></h4>' +
              '<h4><a>Hulk Hogan</a></h4>' +
              '<h4><a>...</a></h4>' +
            '</div>' +
            '<div class="col-xs-12 col-sm-4">' +
              '<h3>L</h3>'+
              '<h4><a>John Lennon</a></h4>' +
              '<h3>M</h3>'+
              '<h4><a>Paul McCartney</a></h4>' +
              '<h3>P</h3>'+
              '<h4><a>Mike Piazza</a></h4>' +
              '<h4><a>...</a></h4>' +
            '</div>' +
            '<div class="col-xs-12 col-sm-4">' +
              '<h3>R</h3>'+
              '<h4><a>Cal Ripken jr</a></h4>' +
              '<h3>S</h3>'+
              '<h4><a>Stone Cold Steve Austin, AICP</a></h4>' +
              '<h4><a>...</a></h4>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Content Two Column With Links',
        image: 'template1.gif',
        description: 'A section overview page pattern for a section of content in 2 columns with headings as links.',
        html:
          '<h3 class="headline-underline">Current Projects</h3>' +
          '<div class="row">' +
              '<div class="col-xs-12 col-sm-6">' +
                '<div class="list-of-links">' +
                  '<h4><a href="#">Hazards Planning: Coastal Zone Management</a></h4>' +
                  '<p>Working with the Coastal States Organization, APA’s hazardrds Planning Research Center will produce a PAS Report on coastal zone management.</p>' +
                  '<h4><a href="#">Growing Food Connections</a></h4>' +
                  '<p>This project will target 20 urban and rural communities across the U.S. that are significantly underserved by the nation’s food system.</p>' +
                  '<h4><a href="#">NOAA Digital Coast</a></h4>' +
                  '<p>A partnership with NOAA to review new planning tools for coastal communities, assist in using and accessing those tools, and in helping advance coastal zone management policy.</p>' +
                '</div>' +
              '</div>' +
              '<div class="col-xs-12 col-sm-6">' +
                '<div class="list-of-links">' +
                  '<h4><a href="#">MoreHazards Planning: Planning Information Exchange</a></h4>' +
                  '<p>In cooperation with ASFPM, APA is conducting a series of quarterly webinars for practitioners on hazard mitigation planning.</p>' +
                  '<h4><a href="#">Hazards Planning: Coastal Zone Management</a></h4>' +
                  '<p>Working with the Coastal States Organization, APA’s Hazards Planning Research Center will produce a PAS Report on coastal zone management.</p>' +
                  '<h4><a href="#">SunShot Solar Outreach Partnership</a></h4>' +
                  '<p>APA and partners will help local and regional governments implement solar energy in their communities. </p>' +
                '</div>' +
              '</div>' +
          '</div>' +
          '<div class="read-more-link"><a href="#">See all Current Research Projects</a></div>'
      },

      {
        title: 'Content 3 Column with Subheadings',
        image: 'template1.gif',
        description: 'A 3-colum content section with subheadings and other basic typography.',
        html:
          '<h2>National Centers for Planning</h2>' +
          '<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed doeiusmod tempor incididunt ut labore et</p>' +
          '<br/>' +
          '<div class="layout-tracery layout-tracery-3col no-top-border no-top-spacing">' +
              '<div class="layout-column">' +
                '<h3 class="headline-underline">Green Communities Center</h3>' +
                '<p>The Green Communities Center advances practices that improve environmental quality, address climate change, and reduce developmental impaces on natural resource.</p>' +
                '<h5>Priorities</h5>' +
                '<ul>' +
                  '<li>Green and Blue Infrastructure</li>' +
                  '<li>Green Energy</li>' +
                  '<li>Green Transportation</li>' +
                '</ul>' +
                '<div class="read-more-link"><a href="#">Learn More</a></div>' +
              '</div>' +
              '<div class="layout-column">' +
                '<h3 class="headline-underline">Hazards Planning Center</h3>' +
                '<p>The Hazards Planning Center advances Practices that promote resilience by reducing the impact of natural hazards on communities and regions.</p>' +
                '<h5>Priorities</h5>' +
                '<ul>' +
                  '<li>Hazard Mitigation</li>' +
                  '<li>Post Disaster Recovery</li>' +
                  '<li>Climation Change Adaption</li>' +
                '</ul>' +
                '<div class="read-more-link"><a href="#">Learn More</a></div>' +
              '</div>' +
              '<div class="layout-column">' +
                '<h3 class="headline-underline">Planning and Community Health Center</h3>' +
                '<p>The Planning and Community Health Center advances practices that improve human environments to promote public health through active living, healthy eating, and health in all planning policies.</p>' +
                '<h5>Priorities</h5>' +
                '<ul>' +
                  '<li>Active Living</li>' +
                  '<li>Food Systems</li>' +
                  '<li>Health in all Planning Policies</li>' +
                '</ul>' +
                '<div class="read-more-link"><a href="#">Learn More</a></div>' +
              '</div>' +
          '</div>'
      },
      {
        title: 'Image Block Float Left',
        image: 'template1.gif',
        description: 'An image block which floats to the left of its container at larger breakpoints at 50% width, for use in blocks of text. Works with captions or without.',
        html:
          '<div class="image-block image-block-float-left">' +
            '<img src="//placehold.it/1000x400" />' +
            '<div class="caption">' +
              '<p>' +
                'Praesent sed hendrerit urna. Proin tempor est vitae erat mattis, quis imperdiet neque ornare.' +
              '</p>' +
            '</div>' +
          '</div>'
      },
      {
        title: 'Image Block Float Right',
        image: 'template1.gif',
        description: 'An image block which floats to the right of its container at larger breakpoints at 50% width, for use in blocks of text. Works with captions or without.',
        html:
          '<div class="image-block image-block-float-right">' +
            '<img src="//placehold.it/1000x400" />' +
            '<div class="caption">' +
              '<p>' +
                'Praesent sed hendrerit urna. Proin tempor est vitae erat mattis, quis imperdiet neque ornare.' +
              '</p>' +
            '</div>' +
          '</div>'
      },
      {
        title: 'Section Page Blog Roll',
        image: 'template1.gif',
        description: 'A variant of Content2ColumnWLinks to display a list of blog posts.',
        html:
          '<h3 class="headline-underline">Blog Posts</h3>' +
          '<div class="row">' +
            '<div class="col-xs-12 col-sm-6">' +
              '<div class="content-preview-list no-top-border no-top-spacing no-bottom-border no-inner-borders">' +
                '<ul>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</a></h4>' +
                  '</li>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Maecenas in nibh nulla. Sed blandit nunc dui. In maximus id mi</a></h4>' +
                  '</li>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Aenean mollis varius sapien, lobortis vestibulum nibh hendrerit at. Maecenas consequat ullamcorper velit, sed scelerisque lorem</a></h4>' +
                  '</li>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Sed non finibus erat. Praesent dignissim enim dui</a></h4>' +
                  '</li>' +
                '</ul>' +
              '</div>' +
            '</div>' +
            '<div class="col-xs-12 col-sm-6">' +
              '<div class="content-preview-list no-top-border no-top-spacing no-bottom-border no-inner-borders">' +
                '<ul>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Phasellus sagittis arcu lectus, vel cursus mauris euismod vel</a></h4>' +
                  '</li>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Donec eu metus in ex feugiat consectetur non a ante. Pellentesque eget sem ac libero</a></h4>' +
                  '</li>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Quisque vestibulum est ut vehicula rhoncus</a></h4>' +
                  '</li>' +
                  '<li class="content-preview-item">' +
                    '<h6 class="content-preview-item-superheadline">January 14, 2016</h6>' +
                    '<h4 class="content-preview-item-headline"><a href="#">Nunc ut nibh nec lectus vulputate congue</a></h4>' +
                  '</li>' +
                '</ul>' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<div class="read-more-link"><a href="#">See all Blog Posts</a></div>'
      },
      {
        title: 'Event Feature',
        image: 'template1.gif',
        description: 'A featured event for a section overview page.',
        html:
          '<div class="layout-tracery">' +
            '<div class="layout-column">' +
              '<div class="row">' +
                '<div class="col-xs-12 col-md-4 col-lg-3">' +
                  '<img src="//placehold.it/600x600" class="img-responsive">' +
                '</div>' +
                '<div class="col-xs-12 col-md-8 col-lg-9">' +
                  '<h2 class="headline-underline">' +
                    '<small>October 28, 2016 | Washington DC, USA</small>' +
                    'AICP Symposiums' +
                  '</h2>' +
                  '<div class="row">' +
                    '<div class="col-xs-12 col-md-12 col-lg-7">' +
                      '<p><strong>AICP sponsors regular symposiums on a variety of topics vital to practicing planners.</strong> This years\' focus is In urban areas, stormwater presents major challenges for water quality. Runoff and combined sewer overflows result in impaired quality and degraded watersheds. Increasingly, green infrastructure approaches can treat and reduce discharge volumes and help mitigate flood risk, in addition to a range of environmental, social, and economic benefits.</p>' +
                      '<p><a href="#" class="btn btn-primary">Register Now</a></p>' +
                      '<br>' +
                    '</div>' +
                    '<div class="col-xs-12 col-md-12 col-lg-5">' +
                      '<h5>Key Speakers</h5>' +
                      '<div class="list-of-speakers">' +
                        '<h4>Paula Conolly, AICP</h4>' +
                        '<p>Policy Strategist, Green City, Clean Waters Program, Philadelphia Water Department</p>' +
                        '<h4>Bethany Bezak, PE, LEED AP</h4>' +
                        '<p>Green Infrastructure Manager, DC Water, DC Clean Rivers Project</p>' +
                        '<h4>Mathy Stanislaus</h4>' +
                        '<p>Assistant Administrator for the Office of Solid Waste and Emergency Response, U.S. EPA</p>' +
                      '</div>' +
                    '</div>' +
                  '</div>' +
                '</div>' +
              '</div>' +
              '<div class="read-more-link">' +
                '<a href="#">Learn more about AICP Symposiums</a>' +
              '</div>' +
            '</div>' +
          '</div>'
      },
      {
        title: 'Bio Box',
        image: 'template1.gif',
        description: 'A single biography.',
        html:
          '<div class="content-preview-item">' +
            '<div class="content-preview-item-image-floated">' +
              '<img src="//placehold.it/200x200">' +
            '</div>' +
            '<h6 class="content-preview-item-superheadline">APA President</h6>' +
            '<h4 class="content-preview-item-headline">Carol Reha, FAICP</h4>' +
            '<div class="content-preview-item-summary">Carol Rhea is a founding partner of the Orion Planning + Design, and previously created and staffed Rhea Consulting. In addition to her work as a consultant, Rhea has worked as a city, county, regional, and state planner. Her passion is helping local governments build planning capacity, and working with small to medium-sized communities to address planning challenges. She has a history of volunteer work that includes serving as a planning commissioner, on a historic foundation board, and in many leadership roles within APA.</div>' +
          '</div>'
      },
      {

        title: 'List of Bios',
        image: 'template1.gif',
        description: 'A list of Bios',
        html:
          '<div class="content-preview-list">' +
            '<ul>' +
              '<li class="content-preview-item">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/200x200">' +
                '</div>' +
                '<h6 class="content-preview-item-superheadline">APA President</h6>' +
                '<h4 class="content-preview-item-headline">Carol Reha, FAICP</h4>' +
                '<div class="content-preview-item-summary">Carol Rhea is a founding partner of the Orion Planning + Design, and previously created and staffed Rhea Consulting. In addition to her work as a consultant, Rhea has worked as a city, county, regional, and state planner. Her passion is helping local governments build planning capacity, and working with small to medium-sized communities to address planning challenges. She has a history of volunteer work that includes serving as a planning commissioner, on a historic foundation board, and in many leadership roles within APA.</div>' +
              '</li>' +
              '<li class="content-preview-item">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/200x200">' +
                '</div>' +
                '<h6 class="content-preview-item-superheadline">President-Elect of APA</h6>' +
                '<h4 class="content-preview-item-headline">Cynthia Bowen, AICP</h4>' +
                '<div class="content-preview-item-summary">Cynthia Bowen is the Director of Planning for Rundell Ernstberger Associates (REA), a national planning, urban design and land architect firm founded in 1979. An active APA member, Bowen has held a number of leadership positions including president of the APA Indiana Chapter and vice chair and secretary/treasurer of the Chapter Presidents Council. Bowen is a graduate of Ball State University with degrees in urban and regional planning and environmental science and design. Within her community, Bowen has served on many boards and committees.</div>' +
              '</li>' +
              '<li class="content-preview-item">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/200x200">' +
                '</div>' +
                '<h6 class="content-preview-item-superheadline">AICP President</h6>' +
                '<h4 class="content-preview-item-headline">Valerie Hubbard, FAICP</h4>' +
                '<div class="content-preview-item-summary">Valerie Hubbard is the director of planning services for Akerman LLP, a national law firm. She provides consulting services to private and public sector clients on a wide variety of planning matters, including comprehensive planning, zoning, permitting, DRIs and land development regulations. Val has held key planning positions in several Florida jurisdictions and was director of community planning for the state land planning agency (2003-2007). Hubbard served as AICP Commissioner from Region III from 2008 until 2014, when she became President-Elect of the AICP Commission. She is current Chair of the AICP Ethics Committee and a past president of the Florida Chapter of APA. Hubbard is a member of the Sunrise Rotary Club in Tallahassee. She has a master\'s degree in Urban and Regional Planning from the University of Florida.</div>' +
              '</li>' +
            '</ul>' +
          '</div>'
      },

      {
        title: 'Responsive Table',
        image: 'template1.gif',
        description: 'Responsive table',
        html:
          '<div class="table-responsive">' +
            '<table class="table">' +
              '<thead>' +
                '<tr>' +
                  '<th>#</th>' +
                  '<th>Firstname</th>' +
                  '<th>Lastname</th>' +
                  '<th>Age</th>' +
                  '<th>City</th>' +
                  '<th>Country</th>' +
                '</tr>' +
              '</thead>' +
              '<tbody>' +
                '<tr>' +
                  '<td>1</td>' +
                  '<td>Anna</td>' +
                  '<td>Pitt</td>' +
                  '<td>35</td>' +
                  '<td>New York</td>' +
                  '<td>USA</td>' +
                '</tr>' +
                '<tr>' +
                  '<td>2</td>' +
                  '<td>John</td>' +
                  '<td>Doe</td>' +
                  '<td>25</td>' +
                  '<td>Florida</td>' +
                  '<td>USA</td>' +
                '</tr>' +
              '</tbody>' +
            '</table>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Sidebar',
        image: 'template1.gif',
        description: 'Grey Container',
        html:
          '<div class="article-content-sidebar slab-gray-bordered">' +
            '<h2>Sidebar title goes here</h2>' +
            '<p class="text-center"><i>By</i> <span class="text-uppercase">Brian Barth</span></p>' +
            '<h4>H4 Subhead Sed ut perspiciatis unde omnis iste natus error sit </h4>' +
            '<p>' +
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamcolaboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum' +
            '</p>' +
            '<div class="image-block">' +
              '<img src="//placehold.it/566x566">' +
              '<div class="caption">' +
                '<p>' +
                 'Aerial view of the port of Redwood City in San Mateo County, California. Photo from U.S. Army Corps of Engineers Digital Visual Library.' +
                '</p>' +
              '</div>' +
            '</div>' +
            '<h4>H4 Lorem ipsum dolor sit amet, consectetur</h4>' +
            '<p>' +
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco' +
            '</p>' +
            '<p>' +
              '<b>Lorem ipsum dolor sit amet, consectetur adipiscing elit:</b>' +
            '</p>' +

            '<ul>' +
              '<li><b>Ut enim ad minima veniam</b>, quis nostrum exercitationem</li>' +
              '<li><b>Ullam corporis suscipit laboriosam</b>, nisi ut aliquid ex ea commodi consequatur?</li>' +
              '<li><b>Quis autem vel eum iure</b> reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur</li>' +
            '</ul>' +

            '<div class="image-block">' +
              '<img src="//placehold.it/566x340">' +
              '<div class="caption">' +
                '<p>' +
                 ' Aerial view of the port of Redwood City in San Mateo County, California. Photo from U.S. Army Corps of Engineers Digital Visual Library.' +
                '</p>' +
              '</div>' +
            '</div>' +

            '</div>'
      },

      {
        title: 'Planning Magazine: Download Issue',
        image: 'template1.gif',
        description: 'Download current issue of Planning Magazine',
        html:
          '<div class="homepage-featured-content-secondary mag-callout">' +
            '<div class="homepage-featured-content-secondary-body">' +
              '<div class="row nested-row">' +
                '<div class="col-lg-3 col-md-3 col-sm-3 col-xs-3">' +
                  '<img src="//placehold.it/113x143" class="img-responsive" alt="Planning magazine image"/>' +
                '</div>' +
                '<div class="col-lg-5 col-md-5 col-sm-5 col-xs-9">' +
                  '<h4>See the entire January issue of Planning Magazine</h4>' +
                '</div>' +
                '<div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">' +
                  '<a href="#" class="btn btn-primary btn-download">Download Now</a>' +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Side by Side Images with Captions',
        image: 'template1.gif',
        description: 'Side by Side Images with Captions',
        html:
          '<div class="article-content-breakout">' +
            '<div class="row">' +
              '<div class="col-sm-6">' +
                '<div class="image-block">' +
                  '<img src="//placehold.it/566x566">' +
                  '<div class="caption">' +
                    '<p>' +
                      'Aerial view of the port of Redwood City in San Mateo County, California. Photo from U.S. Army Corps of Engineers Digital Visual Library.' +
                    '</p>' +
                  '</div>' +
                '</div>' +
              '</div>' +
              '<div class="col-sm-6">' +
                '<div class="image-block">' +
                  '<img src="//placehold.it/566x566">' +
                  '<div class="caption">' +
                    '<p>' +
                      'Aerial view of the port of Redwood City in San Mateo County, California. Photo from U.S. Army Corps of Engineers Digital Visual Library.' +
                    '</p>' +
                  '</div>' +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Full Width Image with Caption',
        image: 'template1.gif',
        description: 'Full Width Image with Caption',
        html:
          '<div class="article-content-breakout">' +
            '<div class="image-block">' +
              '<img src="//placehold.it/1164x655">' +
              '<div class="caption">' +
                '<p>' +
                  'The Taco Bell Cantina in Newport Beach, California, opened in 2017 and was the prototype for the chain’s new concept: restaurants with beer on tap and no drivethrough windows. Courtesy Taco Bell' +
                '</p>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Float Left Image with Caption within Copy',
        image: 'template1.gif',
        description: 'Float Left Image with Caption within Copy',
        html:
          '<div class="clearfix">' +
            '<div class="image-block image-block-float-left">' +
              '<img src="//placehold.it/426x426" alt="Article image" class="img-responsive" />' +
              '<div class="caption">' +
                '<p>Ut porta, sapien at consequat accumsan, purus neque semper quam, vitae consectetur mi mauris sit amet nisi. Cras sit amet ante dapibus, posuere purus quis, ultricies metus.</p>' +
              '</div>' +
            '</div>' +
            '<p>' +
              'The future of fast-food typologies is by no means set in stone, as technological innovations may produce unexpected outcomes. Many fast-food franchises now designate parking areas. The advent of “dark” or “ghost” kitchens—restaurants catering exclusively to online delivery platforms, which eliminate the need for a retail storefront—may prove to be the biggest paradigm shift to hit the industry as it enters its second century. “The future of fast food may look more like a distribution warehouse in a light manufacturing district,” Boone predicts.' +
            '</p>' +
            '<p>' +
              'For customers who have ordered online, where workers dash out to cars with their orders, carhop-style. Delivery services are raising the bar of customer convenience, while likely adding to the carbon emissions of each meal; rather than you swinging by the restaurant on your way home from work, the Uber Eats driver is making a dedicated trip from the restaurant to your home. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamcolaboris nisi ut aliquip ex' +
            '</p>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Float Right Image with Caption within Copy',
        image: 'template1.gif',
        description: 'Float Right Image with Caption within Copy',
        html:
          '<div class="clearfix">' +
            '<div class="image-block image-block-float-right">' +
              '<img src="//placehold.it/426x426" alt="Article image" class="img-responsive" />' +
              '<div class="caption">' +
                '<p>Ut porta, sapien at consequat accumsan, purus neque semper quam, vitae consectetur mi mauris sit amet nisi. Cras sit amet ante dapibus, posuere purus quis, ultricies metus.</p>' +
              '</div>' +
            '</div>' +
            '<p>' +
              'The future of fast-food typologies is by no means set in stone, as technological innovations may produce unexpected outcomes. Many fast-food franchises now designate parking areas. The advent of “dark” or “ghost” kitchens—restaurants catering exclusively to online delivery platforms, which eliminate the need for a retail storefront—may prove to be the biggest paradigm shift to hit the industry as it enters its second century. “The future of fast food may look more like a distribution warehouse in a light manufacturing district,” Boone predicts.' +
            '</p>' +
            '<p>' +
              'For customers who have ordered online, where workers dash out to cars with their orders, carhop-style. Delivery services are raising the bar of customer convenience, while likely adding to the carbon emissions of each meal; rather than you swinging by the restaurant on your way home from work, the Uber Eats driver is making a dedicated trip from the restaurant to your home. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamcolaboris nisi ut aliquip ex' +
            '</p>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Timeline Ladder',
        image: 'template1.gif',
        description: 'Sequence of text/image blocks, alternating flush left/right',
        html:
          '<div class="article-content-timeline slab-gray-bordered">' +
           ' <h2>Timeline title goes here</h2>' +
            '<div class="row">' +
              '<div class="col-sm-6 content-preview-item content-preview-item-data-block content-preview-item-data-block-image-floated-reverse">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/144x144" />' +
                '</div>' +
                '<div class="content-preview-item-summary">' +
                '<b class="date">1920</b>' +
                '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                 '</p>' +
                '</div>' +
              '</div>' +
            '</div>' +
            '<div class="row">' +
              '<div class="col-sm-6 col-sm-offset-6 content-preview-item content-preview-item-data-block">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/144x144" />' +
                '</div>' +
                '<div class="content-preview-item-summary">' +
                '<b class="date">1921</b>' +
                '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                 '</p>' +
                '</div>' +
              '</div>' +
            '</div>' +
            '<div class="row">' +
              '<div class="col-sm-6 content-preview-item content-preview-item-data-block content-preview-item-data-block-image-floated-reverse">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/144x144" />' +
                '</div>' +
                '<div class="content-preview-item-summary">' +
                '<b class="date">1922</b>' +
                '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                 '</p>' +
                '</div>' +
              '</div>' +
            '</div>' +
            '<div class="row">' +
              '<div class="col-sm-6 col-sm-offset-6 content-preview-item content-preview-item-data-block">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/144x144" />' +
                '</div>' +
                '<div class="content-preview-item-summary">' +
                '<b class="date">1923</b>' +
                '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                 '</p>' +
                '</div>' +
              '</div>' +
            '</div>' +

            '<div class="row timeline-bottom-text">' +
              '<div class="col-md-12 col-sm-12">' +
              '<p>' +
               'A building submerged in flooding after Hurricane Laura swept through Carlyss, Louisiana, in August 2020. Photo by Matthew Busch/The New York Times.' +
               '</p>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Stat Shot',
        image: 'template1.gif',
        description: 'Sequence of text/image blocks, alternating image left/right, with percentages',
        html:
          '<div class="article-data-block row">' +
            '<div class="col-sm-8 col-sm-offset-2">' +
              '<div class="content-preview-item content-preview-item-data-block">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/144x144" />' +
                '</div>' +
                '<div class="content-preview-item-summary">' +
                  '<b class="data">90%</b>' +
                  '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                  '</p>' +
                '</div>' +
              '</div>' +

              '<div class="content-preview-item content-preview-item-data-block content-preview-item-data-block-image-floated-reverse">' +
                '<div class="content-preview-item-image-floated">' +
                  '<img src="//placehold.it/144x144" />' +
                '</div>' +
                '<div class="content-preview-item-summary">' +
                  '<b class="data">90%</b>' +
                  '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                  '</p>' +
                '</div>' +
              '</div>' +

              '<div class="content-preview-item content-preview-item-data-block content-preview-item-data-block-underline">' +
                '<div class="content-preview-item-summary">' +
                  '<b class="data">90%</b>' +
                  '<p>' +
                    'White Castle, considered the nation’s first modern fast-food restaurant, opens in Wichita, Kansas.' +
                  '</p>' +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>'
      },

      {
        title: 'Planning Magazine: Content Callout',
        image: 'template1.gif',
        description: 'Links to more information about a topic',
        html:
          '<!-- Content callout example -->' +
          '<div class="content-preview-item layout-tracery content-callout">' +
            '<div class="layout-column">' +
              '<div class="content-preview-item-image-floated">' +
                '<img alt="" class="planning-media" data-content-id="699301" src="https://planning-org-uploaded-media.s3.amazonaws.com:443/image/Planning-2021-04-image23v2.gif" title="Planning Spring 2021 Public Realm">' +
              '</div>' +
              '<h4 class="content-preview-item-headline">Further Impacts: Public Realm</h4>' +
              '<div class="content-preview-item-summary">' +
                'Social media organizing is influencing popular awareness and eliciting responses from governments and organizations. Public dialogues are often simultaneously manifested in public spaces.' +
              '</div>' +
              '<h6>See Also:</h6>' +
              '<div class="content-preview-item-summary"><a href="#">7 Emerging Tips for Equitable Digital Engagement</a>: Despite the ever-present digital divide, inclusive public outreach and social distancing are not mutually exclusive.<br>' +
                '<br>' +
                '<a href="#">Keeping It Legal on Social</a>: Social media is a great way to engage residents and disseminate information, but it poses several legal risks that public agencies need to understand.' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<!-- sample buffer text added -->' +
          '<p>' +
            'As a reliable generator of sales tax revenue, and as a provider of jobs for those who might otherwise struggle to find employment, fast food has long had an upper hand in arguing for the lax land-use regulations that enable the strip-style development pattern that favors drive-through businesses. As urban design ideals and best practices have shifted to embrace walkability and “Main Street”' +
          '</p>' +
          '<!-- content callout example END -->'
      }
    ]
});
