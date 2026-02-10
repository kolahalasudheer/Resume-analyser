"""
ATS Forge - Streamlit Web Application

Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os
import json
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ats.engine import run_ats
from ats.rule_based.scorer import Layer1Scorer
from utils.report_generator import ReportGenerator

# Page config
st.set_page_config(
    page_title="ATS Forge - Resume Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .score-card {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 10px;
    }
    .grade-A { background-color: #90EE90; color: #006400; }
    .grade-B { background-color: #87CEEB; color: #00008B; }
    .grade-C { background-color: #FFD700; color: #8B4513; }
    .grade-D { background-color: #FFA500; color: #8B0000; }
    .grade-F { background-color: #FF6B6B; color: #8B0000; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'results' not in st.session_state:
    st.session_state.results = None

# Header
st.markdown('<div class="main-header">🎯 ATS Forge</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered Resume Analysis for ATS Optimization</p>', unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    # API Key Management
    st.header("🔑 API Configuration")
    
    # Check if API key exists in environment
    env_api_key = os.getenv("GEMINI_API_KEY")
    
    if env_api_key:
        st.success("✅ Environment API key detected")
        use_env_key = st.checkbox("Use environment API key", value=True, key="use_env_key")
        
        if not use_env_key:
            user_api_key = st.text_input(
                "Your Gemini API Key:",
                type="password",
                help="Get your free API key from https://makersuite.google.com/app/apikey",
                key="user_api_key_input"
            )
            if user_api_key:
                os.environ["GEMINI_API_KEY"] = user_api_key
                st.success("✅ Using your custom API key")
    else:
        st.warning("⚠️ No environment API key found")
        user_api_key = st.text_input(
            "Enter your Gemini API Key:",
            type="password",
            help="Get your free API key from https://makersuite.google.com/app/apikey",
            key="user_api_key_input"
        )
        
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key
            st.success("✅ API key configured!")
            st.info("💡 AI features enabled")
        else:
            st.error("❌ AI features disabled")
            with st.expander("How to get API key?"):
                st.markdown("""
                1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
                2. Sign in with Google account
                3. Click "Create API Key"
                4. Copy and paste above
                
                **Note:** API key is free and not shared with others.
                """)
    
    # API Usage Tracking
    if os.getenv("GEMINI_API_KEY"):
        st.markdown("### 📊 API Usage")
        
        # Initialize usage tracker in session state
        if 'api_usage_tracker' not in st.session_state:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from utils.api_usage_tracker import APIUsageTracker
            st.session_state.api_usage_tracker = APIUsageTracker()
        
        tracker = st.session_state.api_usage_tracker
        quota_info = tracker.get_quota_info()
        
        # Display usage with progress bar
        if quota_info['status'] != 'no_key':
            percentage = quota_info['percentage_used']
            
            # Color based on usage
            if percentage < 50:
                bar_color = "normal"
            elif percentage < 80:
                bar_color = "normal"  # Streamlit doesn't support custom colors easily
            else:
                bar_color = "normal"
            
            st.progress(min(percentage / 100, 1.0))
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Requests Used", quota_info['requests_used'])
            with col_b:
                st.metric("Daily Limit", quota_info['daily_limit'])
            
            # Status message
            if quota_info['status'] == 'ok':
                st.success(f"✅ {percentage:.1f}% used - Plenty remaining")
            elif quota_info['status'] == 'warning':
                st.warning(f"⚠️ {percentage:.1f}% used - Monitor usage")
            elif quota_info['status'] == 'critical':
                st.error(f"🔴 {percentage:.1f}% used - Get new key soon!")
            
            st.caption("💡 Free tier: ~1500 requests/day")
            
            if st.button("🔄 Reset Counter", help="Reset usage counter (for testing)"):
                tracker.reset_daily_usage()
                st.rerun()
    
    st.divider()
    
    st.header("📋 About")
    st.info("""
    **ATS Forge** analyzes your resume against job descriptions to help you pass Applicant Tracking Systems (ATS).
    
    **Features:**
    - 🔍 Keyword matching
    - 📄 Formatting validation
    - ✅ ATS compliance check
    - 📊 Detailed scoring
    - 💡 Actionable recommendations
    """)
    
    st.header("🚀 How to Use")
    st.markdown("""
    1. Upload your resume (PDF)
    2. Paste the job description
    3. Click "Analyze Resume"
    4. Review your results!
    """)
    
    st.divider()
    st.caption("Powered by Layer 1 Rule Engine")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose your resume PDF",
        type=['pdf'],
        help="Upload a PDF version of your resume"
    )
    
    if uploaded_file:
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB")

with col2:
    st.subheader("📋 Job Description")
    jd_text = st.text_area(
        "Paste the job description here",
        height=300,
        placeholder="""Paste the full job description including:
- Required skills
- Preferred qualifications
- Responsibilities
- Company info
        """,
        help="Include the complete job posting for best results"
    )

# Analyze button
st.divider()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_button = st.button(
        "🚀 Analyze Resume",
        type="primary",
        use_container_width=True,
        disabled=not (uploaded_file and jd_text)
    )

# Analysis
if analyze_button:
    if not uploaded_file:
        st.error("❌ Please upload a resume PDF")
    elif not jd_text:
        st.error("❌ Please paste a job description")
    else:
        with st.spinner("🔍 Analyzing your resume... This may take a few seconds..."):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Run analysis (Hybrid Mode)
                results = run_ats(resume_path=tmp_path, job_description=jd_text, mode="hybrid")
                
                # Check formatting of results (should contain rule_based part)
                if 'rule_based' in results and results['rule_based']:
                    # Extract the rule-based part for existing UI compatibility
                    rule_results = results['rule_based']
                    # Keep the hybrid score as the main score
                    rule_results['score']['total_score'] = results['final_score']
                    # Add AI insights to the result object for display
                    if results.get('ai_based'):
                         rule_results['ai_insights'] = results['ai_based']
                    
                    # Store JD analysis separately
                    st.session_state.jd_analysis = results.get('jd_analysis', {})
                    # Store project analysis
                    st.session_state.project_analysis = results.get('project_analysis', {})
                    st.session_state.results = rule_results
                else:
                    st.error("Analysis returned incomplete results.")
                
                st.session_state.analysis_done = True
                
                # Clean up temp file
                os.unlink(tmp_path)
                
                st.success("✅ Hybrid Analysis complete!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                import traceback
                with st.expander("See error details"):
                    st.code(traceback.format_exc())

# Display results
if st.session_state.analysis_done and st.session_state.results:
    results = st.session_state.results
    score = results['score']
    kw_match = results['keyword_analysis']['match_results']
    jd_analysis = results['keyword_analysis'].get('jd_analysis')
    
    
    st.divider()
    
    # Info about separate pages
    st.info("💡 **Tip:** Check the sidebar for detailed JD Analysis and Project Optimization pages!")
    
    st.header("📊 Resume Match Results")
    
    # AI Insights Section - Clean bullet format
    if results.get('ai_insights'):
        ai_data = results['ai_insights']
        
        st.markdown("### 🤖 AI Analysis Summary")
        summary = ai_data.get('summary', 'No summary provided')
        # Convert summary to bullet points
        if summary and summary != 'No summary provided':
            summary_sentences = [s.strip() + '.' for s in summary.replace('.', '.|').split('|') if s.strip()]
            for sentence in summary_sentences:
                st.markdown(f"• {sentence}")
        else:
            st.info("No AI summary available")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ AI Identified Strengths")
            for s in ai_data.get('strengths', []):
                st.success(f"• {s}")
        with col2:
            st.markdown("#### ⚠️ AI Identified Weaknesses")
            for w in ai_data.get('weaknesses', []):
                st.warning(f"• {w}")
        
        st.markdown("---")
    
    # PROJECT ANALYSIS SECTION
    if 'project_analysis' in st.session_state and st.session_state.project_analysis:
        proj_data = st.session_state.project_analysis
        
        if proj_data.get('projects'):
            st.header("📂 Project Analysis & Optimization")
            
            # Overall metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Overall Project Score", f"{proj_data.get('overall_score', 0)}/100")
            with col2:
                st.metric("📁 Total Projects", proj_data.get('total_projects', 0))
            with col3:
                avg_relevance = sum(p['relevance_score'] for p in proj_data['projects']) / len(proj_data['projects'])
                st.metric("🎯 Avg Relevance", f"{avg_relevance:.1f}%")
            
            # Recommendations
            if proj_data.get('recommendations'):
                st.markdown("### 💡 Recommendations")
                for rec in proj_data['recommendations']:
                    st.info(rec)
            
            st.markdown("---")
            
            # Individual project analysis
            for idx, project in enumerate(proj_data['projects'], 1):
                # Determine tier color
                relevance = project['relevance_score']
                if relevance >= 70:
                    tier_emoji = "🟢"
                    tier_label = "HIGHLY RELEVANT"
                elif relevance >= 30:
                    tier_emoji = "🟡"
                    tier_label = "MODERATELY RELEVANT"
                else:
                    tier_emoji = "🔴"
                    tier_label = "NOT RELEVANT"
                
                with st.expander(f"{tier_emoji} **Project {idx}: {project['title']}** ({tier_label} - {project['relevance_score']}/100)", expanded=(idx == 1)):
                    
                    # Project metadata
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption(f"**Duration:** {project.get('duration', 'Not specified')}")
                        st.caption(f"**Tech/Course:** {project.get('tech_or_course', 'N/A')}")
                    with col_b:
                        st.caption(f"**Keyword Match:** {project['keyword_match_pct']:.1f}%")
                        st.caption(f"**Matched Keywords:** {len(project.get('matched_keywords', []))}")
                    
                    # AI Overall Advice
                    suggestions_data = project.get('suggestions', {})
                    if isinstance(suggestions_data, dict):
                        overall_advice = suggestions_data.get('overall_advice', '')
                        recommendation = suggestions_data.get('recommendation', '')
                        
                        if overall_advice:
                            if recommendation == 'keep_and_optimize':
                                st.success(f"✅ **AI Recommendation:** {overall_advice}")
                            elif recommendation == 'enhance_with_features':
                                st.warning(f"⚠️ **AI Recommendation:** {overall_advice}")
                            else:
                                st.error(f"🔴 **AI Recommendation:** {overall_advice}")
                    
                    # Keyword analysis
                    if project.get('matched_keywords'):
                        st.markdown("**✅ Matched JD Keywords:**")
                        st.success(", ".join(project['matched_keywords'][:10]))
                    
                    if project.get('missing_keywords'):
                        st.markdown("**⚠️ Missing JD Keywords:**")
                        st.warning(", ".join(project['missing_keywords'][:10]))
                    
                    st.markdown("---")
                    
                    # Original bullets
                    st.markdown("#### 📝 Current Bullets")
                    for bullet in project['bullets']:
                        st.markdown(f"• {bullet}")
                    
                    # AI Suggestions based on tier
                    if isinstance(suggestions_data, dict):
                        # Tier 1 & 2: Bullet improvements
                        bullet_suggestions = suggestions_data.get('suggestions', [])
                        if bullet_suggestions:
                            st.markdown("#### ✨ AI-Optimized Suggestions")
                            
                            for sug_idx, suggestion in enumerate(bullet_suggestions, 1):
                                is_proposed = suggestion.get('is_proposed_addition', False)
                                
                                if is_proposed:
                                    st.markdown(f"**💡 Proposed Addition {sug_idx}:** (Implement this feature first)")
                                else:
                                    st.markdown(f"**Suggestion {sug_idx}:**")
                                
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    st.markdown("*Original:*")
                                    st.text_area(
                                        f"orig_{idx}_{sug_idx}",
                                        suggestion.get('original', ''),
                                        height=80,
                                        disabled=True,
                                        label_visibility="collapsed"
                                    )
                                with col2:
                                    st.markdown("*Improved:*")
                                    st.text_area(
                                        f"improved_{idx}_{sug_idx}",
                                        suggestion.get('improved', ''),
                                        height=80,
                                        key=f"improved_text_{idx}_{sug_idx}",
                                        label_visibility="collapsed"
                                    )
                                
                                # Show what was added
                                if suggestion.get('added_keywords'):
                                    st.caption(f"✅ Added keywords: {', '.join(suggestion['added_keywords'])}")
                                if suggestion.get('improvement_reason'):
                                    st.caption(f"💡 {suggestion['improvement_reason']}")
                                
                                st.markdown("---")
                        
                        # Tier 2: Feature additions
                        feature_additions = suggestions_data.get('feature_additions', [])
                        if feature_additions:
                            st.markdown("#### 🚀 Suggested Feature Additions")
                            st.info("These are small features you can add to improve JD alignment:")
                            
                            for feat_idx, feature in enumerate(feature_additions, 1):
                                st.markdown(f"**Feature {feat_idx}: {feature.get('feature', 'N/A')}**")
                                st.markdown(f"- **Tech Stack:** {feature.get('tech_stack', 'N/A')}")
                                st.markdown(f"- **Why:** {feature.get('reason', 'N/A')}")
                                st.markdown(f"- **Effort:** {feature.get('estimated_effort', 'N/A')}")
                                st.markdown("")
                        
                        # Tier 3: Alternative projects
                        alternative_projects = suggestions_data.get('alternative_projects', [])
                        if alternative_projects:
                            st.markdown("#### 🔄 Alternative Project Suggestions")
                            st.warning("This project has low JD alignment. Consider these alternatives:")
                            
                            for alt_idx, alt_proj in enumerate(alternative_projects, 1):
                                st.markdown(f"**Alternative {alt_idx}: {alt_proj.get('title', 'N/A')}**")
                                st.markdown(f"- **Description:** {alt_proj.get('description', 'N/A')}")
                                st.markdown(f"- **Technologies:** {', '.join(alt_proj.get('key_technologies', []))}")
                                st.markdown(f"- **Expected Impact:** {alt_proj.get('expected_impact', 'N/A').upper()}")
                                st.markdown("")
                        
                        # Copy-paste optimized version (only for Tier 1 & 2)
                        if bullet_suggestions and recommendation != 'consider_replacing':
                            st.markdown("#### 📋 Copy-Paste Optimized Version")
                            optimized_bullets = "\n".join([f"- {sug.get('improved', '')}" for sug in bullet_suggestions])
                            optimized_project = f"""**{project['title']}** | {project.get('tech_or_course', 'Technology')}
{project.get('duration', 'Month/Year - Month/Year')}

{optimized_bullets}
"""
                            st.code(optimized_project, language="markdown")
                            
                            if any(sug.get('is_proposed_addition') for sug in bullet_suggestions):
                                st.caption("⚠️ **Note:** Some suggestions are proposed additions. Implement these features before using in your resume.")
                            else:
                                st.caption("👆 Copy this optimized version to your resume")
            
            st.markdown("---")
        else:
            st.info("ℹ️ No projects found in resume or analysis unavailable")
    

    
    # Overall score
    grade = score['grade']
    grade_class = f"grade-{grade[0]}"  # A, B, C, D, or F
    
    st.markdown(f"""
    <div class="score-card {grade_class}">
        🎯 Final Hybrid Score: {score['total_score']}/100
        <br>
        <span style="font-size: 1rem;">(60% Rule-Based / 40% AI)</span>
        <br>
        Grade: {grade}
    </div>
    """, unsafe_allow_html=True)
    
    # Score breakdown
    st.subheader("📈 Score Breakdown")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🔍 Keyword Match",
            f"{score['keyword_score']}/100",
            delta=f"{kw_match['match_percentage']}% match"
        )
    
    with col2:
        st.metric(
            "📄 Formatting",
            f"{score['formatting_score']}/100",
            delta="ATS-friendly" if score['formatting_score'] >= 90 else "Needs improvement"
        )
    
    with col3:
        st.metric(
            "✅ ATS Compliance",
            f"{score['ats_score']}/100",
            delta="Good" if score['ats_score'] >= 80 else "Review needed"
        )
    
    # Tabs for detailed results
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Keywords", "💪 Strengths & Weaknesses", "💡 Recommendations", "📋 Full Report"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 All Skills in Your Resume")
            st.caption("Sorted by importance to this JD")
            
            skills_with_importance = kw_match.get('resume_skills_with_importance', [])
            
            if skills_with_importance:
                # Group by importance level
                must_keep = [s for s in skills_with_importance if s['importance'] == 100]
                optional = [s for s in skills_with_importance if s['importance'] < 100]
                
                if must_keep:
                    st.markdown("**🎯 Must Keep (Matches JD):**")
                    for skill_info in must_keep:
                        st.markdown(f"- ✅ **{skill_info['skill']}** - {skill_info['importance']}% Match")
                
                if optional:
                    st.markdown(f"\n**📌 Optional Skills (Not required by this JD):**")
                    for skill_info in optional[:15]:  # Show first 15
                        st.markdown(f"- ℹ️ {skill_info['skill']} - {skill_info['importance']}% Relevance")
                    if len(optional) > 15:
                        with st.expander(f"Show all {len(optional)} optional skills"):
                            for skill_info in optional[15:]:
                                st.markdown(f"- ℹ️ {skill_info['skill']} - {skill_info['importance']}% Relevance")
            else:
                st.info("No skills found in resume")
            
            # Explanation
            st.info("""
            **How to use this:**
            - **100% = Must Keep**: Skill is required by the JD
            - **40% = Optional**: Valid skill, but not in this JD (shows broader expertise)
            - **30% = Optional**: Specialized skill not in our database
            
            Keep all 100% skills and review optional skills based on relevance to the target role.
            """)
        
        with col2:
            st.subheader("❌ Missing from Resume")
            st.caption("Skills required by JD but not in your resume")
            
            missing_tech = kw_match['missing_keywords']['tech_skills']
            missing_soft = kw_match['missing_keywords']['soft_skills']
            
            if missing_tech:
                st.markdown("**Technical Skills:**")
                for skill in missing_tech[:15]:
                    st.markdown(f"- ❌ {skill}")
                if len(missing_tech) > 15:
                    st.caption(f"... and {len(missing_tech) - 15} more")
            
            if missing_soft:
                st.markdown("**Soft Skills:**")
                for skill in missing_soft[:5]:
                    st.markdown(f"- ❌ {skill}")
            
            if not missing_tech and not missing_soft:
                st.success("All JD keywords matched!")
        
        # Keyword stats
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        must_keep_count = len([s for s in skills_with_importance if s['importance'] == 100])
        optional_count = len([s for s in skills_with_importance if s['importance'] < 100])
        
        col1.metric("Must Keep Skills", must_keep_count)
        col2.metric("Optional Skills", optional_count)
        col3.metric("Missing from Resume", kw_match['total_missing'])
        col4.metric("JD Match %", f"{kw_match['match_percentage']}%")

        # --- Interactive Editing ---
        st.divider()
        st.subheader("✏️ Interactive Edit")
        with st.expander("Modify Found Skills (Beta)"):
            st.info("If the AI missed a skill or found one incorrectly, you can adjust it here.")
            
            # Get current lists
            current_tech = kw_match['found_keywords']['tech_skills']
            current_missing = kw_match['missing_keywords']['tech_skills']
            
            # Multi-selects for editing
            new_tech = st.multiselect(
                "Found Technical Skills",
                options=sorted(list(set(current_tech + current_missing))),
                default=current_tech,
                help="Add skills that were missed or remove incorrect ones"
            )
            
            if st.button("🔄 Recalculate Score"):
                # Update found keywords
                kw_match['found_keywords']['tech_skills'] = new_tech
                
                # Update missing keywords (inverse of found)
                kw_match['missing_keywords']['tech_skills'] = [
                    k for k in current_missing + current_tech 
                    if k not in new_tech and k in current_missing # Only checking against originally known missing
                ]
                # Simpler: just recalulate missing based on JD tech skills
                jd_tech = results['keyword_analysis']['jd_keywords']['tech_skills']
                kw_match['missing_keywords']['tech_skills'] = [k for k in jd_tech if k not in new_tech]

                # Update stats
                total_jd = kw_match['total_jd_keywords']
                # Approximation: we assume soft skills didn't change for match % calc
                # In a real app we'd track everything. capturing simplified logic here.
                found_all = set(new_tech) | set(kw_match['found_keywords']['soft_skills'])
                kw_match['match_percentage'] = round((len(found_all) / total_jd * 100), 2) if total_jd > 0 else 0

                # Recalculate Score
                scorer = Layer1Scorer()
                new_scores = scorer.calculate_score(
                    kw_match,
                    results['formatting_analysis'],
                    results['ats_analysis']
                )
                
                # Update session state
                st.session_state.results['score'] = new_scores
                
                # Regenerate recommendations
                new_recs = scorer.generate_recommendations(
                    kw_match,
                    results['formatting_analysis'],
                    results['ats_analysis']
                )
                
                # Format recommendations (replicate logic from RuleEngine)
                formatted_recs = []
                for rec in new_recs:
                    formatted_recs.append(f"[{rec['priority'].upper()}] {rec['category']}: {rec['message']}")
                st.session_state.results['recommendations'] = formatted_recs
                
                st.success("✅ Score updated!")
                st.rerun()
    
    with tab2:
        col1, col2 = st.columns(2)
        
        breakdown = score['breakdown']
        
        with col1:
            st.subheader("💪 Strengths")
            if breakdown['strengths']:
                for strength in breakdown['strengths']:
                    st.success(f"✓ {strength}")
            else:
                st.info("No specific strengths identified")
        
        with col2:
            st.subheader("⚠️ Areas to Improve")
            if breakdown['weaknesses']:
                for weakness in breakdown['weaknesses']:
                    st.warning(f"⚠ {weakness}")
            else:
                st.success("No major weaknesses found!")
    
    with tab3:
        st.subheader("💡 Recommendations")
        
        if results['recommendations']:
            for i, rec in enumerate(results['recommendations'], 1):
                # Parse priority
                if '[HIGH]' in rec or '[CRITICAL]' in rec:
                    st.error(f"**{i}. {rec}**")
                elif '[MEDIUM]' in rec:
                    st.warning(f"{i}. {rec}")
                else:
                    st.info(f"{i}. {rec}")
        else:
            st.success("🎉 Your resume looks great! No recommendations needed.")
    
    with tab4:
        st.subheader("📋 Complete Analysis Report")
        
        # Metadata
        st.markdown("**Resume Metadata:**")
        metadata = results['metadata']
        st.json({
            'File': metadata['resume_file'],
            'Pages': metadata['pages'],
            'Format': metadata['format'],
            'Analyzed': metadata['analyzed_at']
        })
        
        # Download button
        report_json = json.dumps(results, indent=2)
        st.download_button(
            label="📥 Download Full Report (JSON)",
            data=report_json,
            file_name=f"ats_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # PDF Report Button
        pdf_bytes = ReportGenerator.generate_pdf(results)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"ats_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
        
        # Expandable full results
        with st.expander("View Full JSON"):
            st.json(results)

# Footer
st.divider()
st.caption("🔒 Your resume is processed locally and not stored anywhere. | Built with ❤️ using ATS Forge Layer 1")
