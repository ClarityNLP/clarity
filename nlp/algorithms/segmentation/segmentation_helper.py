#!/usr/bin/env python3
"""

This is a helper module for segmentation.py.

For import only.

"""

import re
import os
import sys
import json
from claritynlp_logging import log, ERROR, DEBUG

try:
    # for normal operation via NLP pipeline
    from algorithms.finder import time_finder as tf
    from algorithms.finder import date_finder as df
    from algorithms.finder import size_measurement_finder as smf
    from algorithms.finder import lab_value_matcher as lvm
except Exception as e:
    log(e, ERROR)
    # If here, this module was executed directly from the segmentation
    # folder for testing. Construct path to nlp/algorithms/finder and
    # perform the imports above. This is a hack to allow an import from
    # higher-level package.
    this_module_dir = sys.path[0]
    pos = this_module_dir.find('/nlp')
    assert -1 != pos
    # get path to nlp/algorithms/finder and append to sys.path
    nlp_dir =  this_module_dir[:pos+4]
    finder_dir = os.path.join(nlp_dir, 'algorithms', 'finder')
    sys.path.append(finder_dir)

    import time_finder as tf
    import date_finder as df
    import size_measurement_finder as smf
    import lab_value_matcher as lvm

_VERSION_MAJOR = 0
_VERSION_MINOR = 6
_MODULE_NAME = 'segmentation_helper.py'

# set to True to enable debug output
_TRACE = False

# regex for locating an anonymized item [** ... **]
_str_anon = r'\[\*\*[^\]]+\]'
_regex_anon = re.compile(_str_anon)

# regex for locating a contrast agent expression
_str_contrast = r'\bContrast:\s+(None|[a-zA-Z]+\s+Amt:\s+\d+(cc|CC)?)'
_regex_contrast = re.compile(_str_contrast)

# regex for locating a field of view expression
_str_fov = r'\bField of view:\s+\d+'
_regex_fov = re.compile(_str_fov)

# start of a numbered section, such as a list, but with no whitespace
# separating the numbers from the adjacent text
_str_list_start_no_space = r'\b(?P<listnum>\d+(\.|\)))(?P<word>[a-zA-Z]+)'
_regex_list_start_no_space = re.compile(_str_list_start_no_space)

# find numbered sentences: look for digits followed by '.' or ')',
# whitespace, then a capital letter starting a word
_str_list_start = r'\b(?P<listnum>\d+(\.|\)))\s+'
_str_list_item = _str_list_start + r'([A-Z][a-z]+|\d)\b'
_regex_list_start = re.compile(_str_list_start)
_regex_list_item  = re.compile(_str_list_item)

# find captialized headers
_str_caps_word = r'\b([123]-?D|[-_A-Z]+|[-_A-Z]+/[-_A-Z]+)\b'
_str_caps_header = r'(' + _str_caps_word + r'\s+)*' + _str_caps_word + r'\s*#?:'
_regex_caps_header = re.compile(_str_caps_header)

# find sentences that end with a dash followed by a word
_str_ending_dashword = r'\-[a-z]+\Z'
_regex_ending_dashword = re.compile(_str_ending_dashword, re.IGNORECASE)

# find sentences that begin with a number list
_str_startswith_number_list = r'\A[\d.,]+\s[\d.,]+'
_regex_startswith_number_list = re.compile(_str_startswith_number_list)

# find sentences that end with an operator
'+', '*', '/', '%', '^', '>=', '>', '<=', '<', '=', '!='
_str_endswith_operator = r'[-+*/%^><=!]\Z'
_regex_endswith_operator = re.compile(_str_endswith_operator)

# find sentences that consist of a single word
_str_single_word = r'\A[-a-z\d.()]+\Z'
_regex_single_word = re.compile(_str_single_word, re.IGNORECASE)

# find concatenated sentences with no space after the period

# need at least two chars before '.', to avoid matching C.Diff, M.Smith, etc.
# neg lookahead prevents capturing inside abbreviations such as Sust.Rel.
_regex_two_sentences = re.compile(r'\b[a-zA-Z]{2,}\.[A-Z][a-z]+(?!\.)')

# prescription abbreviations
_str_prescription_abbrev = r'\b(a\.c|a\.d|ad\.? lib|admov|agit|alt\. h|'    +\
    r'am[pt]|aq|a\.l|a\.s|a\.t\.c|a\.u|b\.i\.d|b\.[ms]|bol|caps?|'          +\
    r'd\.a\.w|dieb\. alt|di[lv]|disp|d\.t\.d|d\.w|elix|e\.m\.p|emuls|'      +\
    r'h\.s|inj|l\.a\.s|liq|lot|mist|n\.m\.t|noct|non rep|n\.t\.e|'          +\
    r'o\.[dsu]|p\.o\./p\.r|p\.[cmor]|pulv|q\.a\.[dm]|q\.h\.s|q\.[dhs]'      +\
    r'q\.\s?\d+h|q\.i\.d|q\.o\.d|qqh|q\.\d+\-\d+h|q\.\d+h|q|'               +\
    r's\.a|sig|sol|s\.o\.s|si op\. sit|ss|stat|supp|susp|syr|'              +\
    r'tab|tal|t\.i\.[dw]|t\.d\.s|t\.p\.n|tinct?|u\.d|u\.t\. dict|'          +\
    r'ung|u\.s\.p|vag|y\.o)[\.:](?![a-z])'
_regex_prescription_abbrev = re.compile(_str_prescription_abbrev,
                                        re.IGNORECASE)
# common drug units
_str_drug_units = r'(mg/[md]?L|mg/g|mg/patch|m[gL]|mcg/hr|mcg/min|'         +\
    r'mEq/L|meq|g|%|units?)\s?'
_str_drug_amt = r'\b\d+\s?' + _str_drug_units
_regex_drug_amt = re.compile(_str_drug_amt, re.IGNORECASE)

# abbreviations
_str_weekday  = r'((Mon|Tues|Wed|Thurs|Thur|Thu|Fri|Sat|Sun)\.)'
_str_h_o      = r'(\.?H/O)'
_str_r_o      = r'(r/o(ut)?)'
_str_with     = r'(w/)'
_str_s_p      = r'(s/p)' # stable pending
_str_r_l      = r'((Right|Left)\s+[A-Z]+)'
_str_sust_rel = r'(Sust\.?\s?Rel\.?)'
_str_y_o      = r'(y[\s.]+o\.?)' # years old
_str_num_hrs  = r'[1-2]?[0-9]\s?h\.?'

_str_abbrev = r'\b(' + _str_weekday + r'|' + _str_h_o      + r'|' +\
    _str_r_o + r'|'  + _str_s_p     + r'|' + _str_with     + r'|' +\
    _str_s_p + r'|'  + _str_r_l     + r'|' + _str_sust_rel + r'|' +\
    _str_y_o + r'|'  + _str_num_hrs + r')'
_regex_abbrev = re.compile(_str_abbrev, re.IGNORECASE)

# gender
_str_gender   = r'\b(sex|gender)\s*:\s*(male|female|m\.?|f\.?)'
_regex_gender = re.compile(_str_gender, re.IGNORECASE)

# recognizes tokens substituted by this code; case sensitive, must match
# the token construction in _make_token below
_str_token = r'\|[A-Z_]+\d+\|'
_str_multi_token = r'(' + _str_token + r'\s?' + r'){2,}'
_regex_multi_token = re.compile(_str_multi_token)

# operators except for '-' that might appear in the text
_operator_set = {
    '+', '*', '/', '%', '^', '>=', '>', '<=', '<', '=', '!='
}

# lists to keep track of token substitutions; add any new to _all_subs
_fov_subs          = []
_anon_subs         = []
_contrast_subs     = []
_size_meas_subs    = []
_header_subs       = []
_prescription_subs = []
_vitals_subs       = []
_abbrev_subs       = []
_gender_subs       = []
_date_subs         = []
_time_subs         = []
_drug_subs         = []
_multi_token_subs  = []

_all_subs = [
    _fov_subs, _anon_subs, _contrast_subs, _size_meas_subs, _header_subs,
    _prescription_subs, _vitals_subs, _abbrev_subs, _gender_subs, _date_subs,
    _time_subs, _drug_subs, _multi_token_subs
]

# This is the start and end character of the replacement token.
# If this is changed, change _fix_broken_tokens and _check_for_tokens below.
_DELIMITER = '&&'


###############################################################################
def enable_debug():
    
    global _TRACE
    _TRACE = True

    #lvm.enable_debug()

    
###############################################################################
def init():

    lvm.init()
    

###############################################################################
def _print_substitutions(tuple_list, banner_text):
    """
    Print text substitutions to stdout; for debug only.
    Tuples are (start_offset, end_offset, match_text).
    """
    
    print('*** {0} ***'.format(banner_text))
    for i, t in enumerate(tuple_list):
        print('[{0:3d}]: [{1:4},{2:4}): {3}'.format(i, t[0], t[1], t[2]))
    print()
        

###############################################################################
def _print_sentence_list(caption, sentence_list):
    """
    Debug only print function.
    """
    
    print('\n{0}: '.format(caption))
    for i, s in enumerate(sentence_list):
        print('[{0:3d}]: {1}'.format(i, s))
    print()


###############################################################################
def _check_for_tokens(sentence_list):
    """
    Scan each sentence for any remaining tokens. After undoing the token
    substitutions no tokens should remain.
    """

    token_regex = re.compile(r'&&[A-Z0-9]+&&')
    
    for s in sentence_list:
        match = token_regex.search(s)
        if match:
            print('segmentation_helper::_check_for_tokens: ' \
                  'FOUND SENTENCE WITH TOKEN: ')
            print(s)
            print()

            # this is a fatal error; no tokens should remain after undoing
            # the token substitutions
            assert False
    
    
###############################################################################
def _fix_broken_tokens(sentence_list):
    """
    Scan the sentence list and find any substitution tokens that might have
    been split apart by the sentence tokenizer. If a token was broken apart
    it will very likely have been split between the '&&' symbols. So look for
    a sentence that ends with an '&' and has the next sentence starting with
    an '&'. If that fails, look for a sentence that starts with '&&' and ends
    with the other piece of the token.
    """

    fixed = [sentence_list[0]]
    for i in range(len(sentence_list)-1):
        s1 = fixed[-1]
        s2 = sentence_list[i+1]
        if s1.endswith('&') and s2.startswith('&'):
            fixed[-1] += s2
        else:
            if s2.startswith(_DELIMITER):
                match = re.search(r'&&[A-Z_]+\d\d\d\d\Z', s1)
                if match:
                    fixed[-1] += s2
            else:
                fixed.append(s2)

    return fixed

    
###############################################################################
def _make_token(token_text, counter):
    """
    Generate a token string for textual replacement.
    """

    token = '{0}{1}{2:04}{3}'.format(_DELIMITER, token_text,
                                     counter, _DELIMITER)
    return token

    
###############################################################################
def _insert_tokens(report, token_text, tuple_list, sub_list):
    """
    The tuple_list is a list of (start, end, match_text) tuples. For each
    tuple in this list, replace report[start:end] with a token created by
    _make_token. Store the substitutions in sub_list and return the new report.
    """

    if 0 == len(tuple_list):
        return report

    # generate tokens for each unique text
    sub_list.clear()
    token_map = dict()

    counter = 0
    for start, end, match_text in tuple_list:
        if match_text in token_map:
            continue
        else:
            token = _make_token(token_text, counter)
            token_map[match_text] = token
            sub_list.append( (token, match_text) )
            counter += 1

    # do token replacements
    new_report = ''
    prev_end = 0
    for start, end, match_text in tuple_list:
        chunk1 = report[prev_end:start]
        assert match_text in token_map
        token = token_map[match_text]
        new_report += chunk1 + token
        prev_end = end
    new_report += report[prev_end:]
        
    return new_report
    
    
###############################################################################
def _find_size_meas_subs(report, sub_list, token_text):
    """
    Run the size measurement finder to find measurements such as 3 cm. x 4 cm.
    The standard NLP sentence tokenizers can incorrectly split such 
    measurements after the first '.'.
    """

    json_string = smf.run(report)
    if '[]' == json_string:
        return report
    
    json_data = json.loads(json_string)

    # unpack JSON result into a list of SizeMeasurement namedtuples
    measurements = [smf.SizeMeasurement(**m) for m in json_data]

    # convert to a list of (start, end, match_text) tuples
    tuple_list = [(m.start, m.end, m.text) for m in measurements]

    if _TRACE:
        _print_substitutions(tuple_list, 'SIZE MEASUREMENTS')

    new_report = _insert_tokens(report, token_text, tuple_list, sub_list)
    return new_report


###############################################################################
def _find_date_subs(report, sub_list, token_text):
    """
    Run date_finder to find dates in the report text and replace with tokens.
    """

    json_string = df.run(report)
    if '[]' == json_string:
        return report

    json_data = json.loads(json_string)

    # unpack JSON result into a list of DateValue namedtuples
    dates = [df.DateValue(**d) for d in json_data]

    # ignore all-digit dates, or all text (such as 'may', 'june', etc.)
    keep_dates = []
    for d in dates:
        if d.text.isdigit():
            continue
        elif re.match(r'\A[a-z]+\Z', d.text, re.IGNORECASE):
            continue
        else:
            keep_dates.append(d)

    dates = keep_dates
            
    # convert to a list of (start, end, match_text) tuples
    # ignore all-digit matches, since could likely be a measured value    
    tuple_list = [(d.start, d.end, d.text) for d in dates
                  if not d.text.isdigit()]

    if _TRACE:
        _print_substitutions(tuple_list, 'DATES')

    new_report = _insert_tokens(report, token_text, tuple_list, sub_list)            
    return new_report


###############################################################################
def _find_time_subs(report, sub_list, token_text):
    """
    Run time_finder to find time expressions in the report text and
    replace with tokens.
    """

    json_string = tf.run(report)
    if '[]' == json_string:
        return report
        
    json_data = json.loads(json_string)

    # unpack JSON result into a list of TimeValue namedtuples
    times = [tf.TimeValue(**t) for t in json_data]

    # convert to a list of (start, end, match_text) tuples
    # ignore any all-digit matches, could be a measured value
    tuple_list = [(t.start, t.end, t.text) for t in times
                  if not t.text.isdigit()]

    if _TRACE:
        _print_substitutions(tuple_list, 'TIMES')

    new_report = _insert_tokens(report, token_text, tuple_list, sub_list)
    return new_report


###############################################################################
def _find_vitals_subs(report, sub_list, token_text):
    """
    Run the lab_value_matcher to find vital signs and replace with tokens.
    """

    # use lab_value_matcher to find all vitals, lab value lists, etc.
    vitals = lvm.run(report)
    tuple_list = [(v.start, v.end, v.match_text) for v in vitals]
    
    if _TRACE:
        _print_substitutions(tuple_list, 'VITALS')
        
    new_report = _insert_tokens(report, token_text, tuple_list, sub_list)
    return new_report
    

###############################################################################
def _find_substitutions(report, regex_or_subs, sub_list, token_text):
    """
    """

    if list != type(regex_or_subs):
        # regex_or_subs is a regex
        regex = regex_or_subs
        tuple_list = []

        iterator = regex.finditer(report)
        for match in iterator:
            tuple_list.append( (match.start(), match.end(), match.group()) )
    else:
        tuple_list = regex_or_subs    
            
    if 0 == len(tuple_list):
        return report

    if _TRACE:
        _print_substitutions(tuple_list, token_text)

    new_report = _insert_tokens(report, token_text, tuple_list, sub_list)
    return new_report
        
        
###############################################################################
def do_substitutions(report):
    """
    """

    # clear all substitution lists
    for sub_list in _all_subs:
        sub_list.clear()

    if _TRACE:
        log('REPORT BEFORE SUBSTITUTIONS: \n' + report + '\n')

    # order matters here...
    report = _find_substitutions(report, _regex_abbrev, _abbrev_subs, 'ABBREV')

    report = _find_vitals_subs(report, _vitals_subs, 'VITALS')
    
    report = _find_substitutions(report, _regex_caps_header,
                                 _header_subs, 'HEADER')

    report = _find_date_subs(report, _date_subs, 'DATE')
    report = _find_time_subs(report, _time_subs, 'TIME')
    
    report = _find_substitutions(report, _regex_anon, _anon_subs, 'ANON')    
    
    report = _find_substitutions(report, _regex_contrast,
                                 _contrast_subs, 'CONTRAST')
    report = _find_substitutions(report, _regex_fov, _fov_subs, 'FOV')
    report = _find_size_meas_subs(report, _size_meas_subs, 'MEAS')
    report = _find_substitutions(report, _regex_prescription_abbrev,
                                 _prescription_subs, 'PRESCRIPTION_ABBREV')
    report = _find_substitutions(report, _regex_gender, _gender_subs, 'GENDER')
    report = _find_substitutions(report, _regex_drug_amt,
                                 _drug_subs, 'DRUG_AMOUNT')
    report = _find_substitutions(report, _regex_multi_token,
                                 _multi_token_subs, 'MULTITOKEN')

    if _TRACE:
        log('REPORT AFTER SUBSTITUTIONS: \n' + report + '\n')

    return report


###############################################################################
def _replace_text(sentence_list, sub_list):
    """
    For each sentence in sentence_list, replace all tokens with the original
    text. The sub_list is a list of tuples of the form
    (substituted_token, original_text).
    """

    if 0 == len(sub_list):
        return sentence_list
    
    for i in range(len(sentence_list)):
        count = 0
        sentence = sentence_list[i]
        for entry in sub_list:
            token = entry[0]
            orig = entry[1]
            # find all occurrences of the token and restore original text
            while -1 != sentence.find(token):
                sentence = sentence.replace(token, orig)
                count += 1

        if count > 0:
            sentence_list[i] = sentence

    return sentence_list
            

###############################################################################
def undo_substitutions(sentence_list):
    """
    Undo the textual substitutions in 'do_substitions', but in the reverse
    order.
    """

    # fix any broken tokens that may have been split by segmentation
    sentence_list = _fix_broken_tokens(sentence_list)
    
    if _TRACE:
        _print_sentence_list('SENTENCE LIST WITH SUBSTITUTIONS', sentence_list)
        
    sentence_list = _replace_text(sentence_list, _multi_token_subs)
    sentence_list = _replace_text(sentence_list, _drug_subs)
    sentence_list = _replace_text(sentence_list, _gender_subs)
    sentence_list = _replace_text(sentence_list, _prescription_subs)
    sentence_list = _replace_text(sentence_list, _size_meas_subs)
    sentence_list = _replace_text(sentence_list, _fov_subs)
    sentence_list = _replace_text(sentence_list, _contrast_subs)
    sentence_list = _replace_text(sentence_list, _anon_subs)
    sentence_list = _replace_text(sentence_list, _time_subs)
    sentence_list = _replace_text(sentence_list, _date_subs)
    sentence_list = _replace_text(sentence_list, _header_subs)
    sentence_list = _replace_text(sentence_list, _vitals_subs)
    sentence_list = _replace_text(sentence_list, _abbrev_subs)

    # ensure that no more tokens remain
    _check_for_tokens(sentence_list)
    
    return sentence_list
        

###############################################################################
def _erase_spans(report, span_list):
    """
    Erase all report chars bounded by each [start, end) span.
    """

    if len(span_list) > 0:
        prev_end = 0
        new_report = ''
        for span in span_list:
            start = span[0]
            end   = span[1]
            new_report += report[prev_end:start]
            prev_end = end
        new_report += report[prev_end:]
        report = new_report

    return report


###############################################################################
def cleanup_report(report):
    """
    Do some basic cleanup operations on the report text.
    """

    # remove (Over) ... (Cont) inserts (found in MIMIC data)
    spans = []
    iterator = re.finditer(r'\(Over\)', report)
    for match_over in iterator:
        start = match_over.start()
        chunk = report[match_over.end():]
        match_cont = re.search(r'\(Cont\)', chunk)
        if match_cont:
            end = match_over.end() + match_cont.end()
            spans.append( (start, end))
            
    report = _erase_spans(report, spans)

    # insert a space between list numbers and subsequent text, makes
    # lists and start-of-sentence negations easier to identify
    prev_end = 0
    new_report = ''
    iterator = _regex_list_start_no_space.finditer(report)
    for match in iterator:
        # end of list num (digits followed by '.' or ')'
        end = match.end('listnum')
        # start of following (concatenated) word
        start = match.start('word')
        new_report += report[prev_end:end]
        new_report += ' '
        prev_end = start
    new_report += report[prev_end:]
    report = new_report

    # Remove long runs of dashes, underscores, stars, or question marks
    report = re.sub(r'[-_*?]{3,}', ' ', report)
    
    # collapse repeated whitespace (including newlines) into a single space
    report = re.sub(r'\s+', ' ', report)

    # collapse multiple '/' into a single '/'
    report = re.sub(r'/+', '/', report)
    
    # convert unicode left and right quotation marks to ascii
    report = re.sub(r'(\u2018|\u2019)', "'", report)
    
    return report
    

###############################################################################
def fixup_sentences(sentence_list):
    """
    Move punctuation from the start of a sentence to the end of the previous
    sentence.
    """

    num = len(sentence_list)
    
    i = 1
    while i < num:
        s = sentence_list[i]
        if s.startswith(':') or s.startswith(','):
            # move to end of previous sentence
            sprev = sentence_list[i-1]
            sentence_list[i-1] = sprev + ':'
            sentence_list[i]   = s[1:].lstrip()
        i += 1

    # need at least two sentences to continue
    if num <= 1:
        return sentence_list

    # Dashes are often used to demarcate phrases. If a sentence ends with a
    # single word preceded by a dash, merge with the following sentence. If a
    # sentence ends with an operator, merge as well.

    merged_sentences = []

    i = 0
    merge_count = 0
    while i < num:
        s = sentence_list[i]
        match1 = _regex_ending_dashword.search(s)
        match2 = _regex_endswith_operator.search(s)
        if match1 or match2 and i < num-1:
            merged_sentences.append(s + ' ' + sentence_list[i+1])
            i += 2
            merge_count += 1
        else:
            merged_sentences.append(s)
            i += 1

    assert len(merged_sentences) + merge_count == num
            
    # check for opportunities to merge a sentence with the previous one
    num = len(merged_sentences)
    results = [merged_sentences[0]]
    merge_count = 0
    for i in range(1, len(merged_sentences)): 
        s = merged_sentences[i].strip()
        
        # Is the first char of the sentence an operator?
        if len(s) < 1:
            continue
        c = s[0]
        starts_with_op = c in _operator_set

        # Does the sentence starts with a list of numbers (and hence
        # no header to identify what the numbers are)?
        match1 = _regex_startswith_number_list.match(s)

        # Does the sentence consist of a single word?
        match2 = _regex_single_word.match(s)
        
        if match1 or match2 or starts_with_op:
            
            if _TRACE:
                log('Appending sentence: "{0}"'.format(s))
            
            results[-1] = results[-1] + ' ' + s
            merge_count += 1
        else:
            results.append(s)

    assert len(results) + merge_count == num
            
    # The Spacy tokenizer tends to break sentences after each period in a
    # numbered list of items. Look for a sequence of sentences with
    # 1., 2., 3., ... at the ends and remove it.
    #
    # Variables i and j form a range of sentences in results[].
    # Variables 'start' and 'end' span the range of the numeric sequence.
    #
    i = 0
    num = len(results)
    while i < num:
        sentence = results[i]
        match = re.search(r' (?P<num>\d+)\.\Z', sentence)
        if not match:
            i += 1
            continue

        start = int(match.group('num'))
        if _TRACE:
            log('List start: {0}.'.format(start))
        
        end = start + 1
        j = i+1
        while end < num and j < num:
            search_str = r' {0}\.\Z'.format(end)
            match = re.search(search_str, results[j])
            if not match:
                break

            if _TRACE:
                log('list item {0}'.format(end))
            end += 1
            j += 1
                
        if end - start > 1:
            # delete sentence-ending numbers from results[i..j-1]
            for k in range(i, j):
                match = re.search(r' \d+\.\Z', results[k])
                assert match
                if _TRACE:
                    log('REMOVED END NUMBER: {0}'.format(results[k]))
                results[k] = results[k][:match.start()]
            i = j + 1
            continue
        else:
            i += 1

    return results


###############################################################################
def split_section_headers(sentence_list):
    """
    Put an all caps section header in a separate sentence from the subsequent
    text.
    """

    sentences = []
    for s in sentence_list:
        subs = []
        iterator = _regex_caps_header.finditer(s)
        for match in iterator:
            subs.append( (match.start(), match.end()) )
        if len(subs) > 0:
            prev_end = 0
            for start, end in subs:
                before = s[prev_end:start].strip()
                header = s[start:end].strip()
                prev_end = end
                if len(before) > 0:
                    sentences.append(before)
                sentences.append(header)
            after = s[prev_end:].strip()
            if len(after) > 0:
                sentences.append(after)
        else:
            sentences.append(s)

    return sentences
        

###############################################################################
def split_concatenated_sentences(sentence_list):
    """
    """

    sentences = []
    for s in sentence_list:
        match = _regex_two_sentences.search(s)
        if match:
            s1 = s[:match.end()]
            s2 = s[match.end():]
            sentences.append(s1)
            sentences.append(s2)
        else:
            sentences.append(s)

    return sentences


###############################################################################
def delete_junk(sentence_list):
    """
    """

    sentences = []
    num = len(sentence_list)

    #for s in sentence_list:
    i = 0
    while i < num:
        s = sentence_list[i]

        # delete any remaining list numbering
        match = _regex_list_start.match(s)
        if match:
            s = s[match.end():]

        # remove any sentences that consist of just '1.', '2.', etc.
        match = re.match(r'\A\s*\d+(\.|\))\s*\Z', s)
        if match:
            i += 1
            continue

        # remove any sentences that consist of '#1', '#2', etc.
        match = re.match(r'\A\s*#\d+\s*\Z', s)
        if match:
            i += 1
            continue

        # remove any sentences consisting entirely of symbols
        match = re.match(r'\A\s*[^a-zA-Z0-9]+\s*\Z', s)
        if match:
            i += 1
            continue

        # merge isolated age + year
        if i < num-1:
            if s.isdigit() and sentence_list[i+1].startswith('y'):
                s = s + ' ' + sentence_list[i+1]
                i += 1

        # if next sentence starts with 'now measures', merge with current
        if i < num-1:
            if sentence_list[i+1].startswith('now measures'):
                s = s + ' ' + sentence_list[i+1]
                i += 1

        sentences.append(s)
        i += 1

    return sentences


###############################################################################
def get_version():
    return '{0} {1}.{2}'.format(_MODULE_NAME, _VERSION_MAJOR, _VERSION_MINOR)

